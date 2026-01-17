"""
Views for Payments app
- Payment processing
- Razorpay integration
- Refund management
- Invoice generation
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Payment, PaymentMethod, Refund, Invoice
from food.models import FoodOrder
from .forms import PaymentForm, RazorpayPaymentForm
from bookings.models import Booking
import razorpay
from razorpay.errors import SignatureVerificationError, BadRequestError
import logging
from django.conf import settings
import uuid
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string
from django.templatetags.static import static
from datetime import timedelta
import hmac
import hashlib
import os
import base64
import urllib.parse


def get_razorpay_client():
    """Return a configured Razorpay client or None if keys are missing/invalid."""
    key_id = (getattr(settings, 'RAZORPAY_KEY_ID', '') or '').strip()
    key_secret = (getattr(settings, 'RAZORPAY_KEY_SECRET', '') or '').strip()
    # Consider keys invalid only if they look like placeholders or are empty
    if not key_id or not key_secret:
        return None
    low_key = key_id.lower()
    low_secret = key_secret.lower()
    if 'your_' in low_key or 'your_' in low_secret or key_id.startswith('paste_'):
        return None

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        # Quick auth check: attempt a lightweight read request to verify credentials
        # This will raise BadRequestError on authentication failure
        try:
            client.order.all({'count': 1})
        except BadRequestError:
            # Authentication failed
            return None
        except Exception:
            # Other transient errors (network) - still return client so code can fallback
            return client
        return client
    except Exception:
        return None


def is_simulation_enabled():
    """Return True when we should simulate Razorpay interactions locally.
    - Check RAZORPAY_FORCE_SIMULATION setting first (explicit control)
    - If not set, simulate only when keys are invalid/placeholder
    """
    force_sim = getattr(settings, 'RAZORPAY_FORCE_SIMULATION', False)
    if force_sim is True:
        return True
    
    # If RAZORPAY_FORCE_SIMULATION is False, use real API (don't simulate)
    if force_sim is False:
        return False
    
    # Fallback: simulate only if client creation would fail
    client = get_razorpay_client()
    return client is None


def compute_signature(order_id: str, payment_id: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature like Razorpay: hmac(order_id|payment_id, secret)"""
    payload = f"{order_id}|{payment_id}".encode('utf-8')
    return hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()


@login_required(login_url='users:login')
def payment_gateway(request, booking_id):
    """
    Display payment gateway for booking
    """
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    if booking.status != 'pending':
        messages.warning(request, 'This booking is not pending payment.')
        return redirect('bookings:booking_detail', pk=booking_id)
    
    # Get or create payment record with required fields
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'amount': booking.final_amount,
            'total_amount': booking.final_amount,
            'currency': 'INR',
        }
    )
    # Update amounts in case booking was modified
    if not created:
        payment.amount = booking.final_amount
        payment.total_amount = booking.final_amount
        payment.save()
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment.payment_method = form.cleaned_data['payment_method']
            payment.status = 'processing'
            payment.save()
            
            # Redirect to Razorpay
            return redirect('payments:razorpay_checkout', payment_id=payment.pk)
        else:
            messages.error(request, 'Error selecting payment method.')
    else:
        form = PaymentForm()
    
    context = {
        'booking': booking,
        'payment': payment,
        'form': form,
        'page_title': 'Payment',
    }
    return render(request, 'payments/payment_gateway.html', context)


@login_required(login_url='users:login')
def payment_methods(request):
    """Show available/saved payment methods to the user."""
    methods = PaymentMethod.objects.filter(is_active=True)
    context = {
        'methods': methods,
        'page_title': 'Payment Methods',
    }
    return render(request, 'payments/payment_methods.html', context)


@login_required(login_url='users:login')
def initiate_payment(request, order_type, order_id):
    """
    Create a Payment record for non-booking orders (e.g. food) and redirect to checkout.
    """
    # For now support only food orders
    if order_type != 'food':
        messages.error(request, 'Unsupported order type for payment.')
        return redirect('food:view_cart')

    food_order = get_object_or_404(FoodOrder, pk=order_id, user=request.user)

    # Create Payment record without a Booking (booking nullable)
    payment = Payment.objects.create(
        booking=None,
        amount=food_order.final_amount,
        total_amount=food_order.final_amount,
        currency='INR',
        status='pending',
        payment_notes=f'food_order:{food_order.pk}'
    )

    return redirect('payments:razorpay_checkout', payment_id=payment.pk)


@login_required(login_url='users:login')
def use_payment_method(request, method_id):
    """Apply a payment method to a pending booking and redirect to checkout.

    Accepts optional query param 'booking' for explicit booking id. If not provided,
    uses the most recent pending booking for the user.
    """
    method = get_object_or_404(PaymentMethod, pk=method_id, is_active=True)

    booking_id = request.GET.get('booking')
    if booking_id:
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        if booking.status != 'pending':
            messages.warning(request, 'Selected booking is not pending payment.')
            return redirect('payments:payment_methods')
    else:
        booking = Booking.objects.filter(user=request.user, status='pending').order_by('-created_at').first()
        if not booking:
            messages.info(request, 'No pending booking found to apply this payment method.')
            return redirect('payments:payment_methods')

    # Get or create Payment record for the booking
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'amount': booking.final_amount,
            'total_amount': booking.final_amount,
            'currency': 'INR',
            'payment_method': method,
            'status': 'pending',
        }
    )

    # If payment existed, update the method and amounts
    payment.payment_method = method
    payment.amount = booking.final_amount
    payment.total_amount = booking.final_amount
    payment.status = 'pending'
    payment.save()

    # Redirect directly to checkout for this payment
    return redirect('payments:razorpay_checkout', payment_id=payment.pk)


@login_required(login_url='users:login')
def razorpay_checkout(request, payment_id):
    """
    Initialize Razorpay payment checkout
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    # authorize access
    if payment.booking:
        if payment.booking.user != request.user:
            return HttpResponseForbidden()
    else:
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
                if not fo or fo.user != request.user:
                    return HttpResponseForbidden()
            except Exception:
                return HttpResponseForbidden()
        else:
            return HttpResponseForbidden()
    
    # Use centralized client factory to validate keys
    client = get_razorpay_client()
    simulate = is_simulation_enabled()

    if simulate:
        # Simulation mode: create a simulated order (no external API call)
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', '') or ''
        razorpay_order = {
            'id': f'sim_order_{payment.pk}',
            'amount': int(payment.total_amount * 100),
        }
        payment.razorpay_order_id = razorpay_order['id']
        payment.save()

        # Map our payment method to Razorpay method (if selected)
        razorpay_method = None
        if payment.payment_method:
            method_map = {
                'credit_card': 'card',
                'debit_card': 'card',
                'upi': 'upi',
                'net_banking': 'netbanking',
                'wallet': 'wallet',
            }
            razorpay_method = method_map.get(payment.payment_method.name)

        # include related food order in context when available
        fo = None
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
            except Exception:
                fo = None

        context = {
            'payment': payment,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': key_id,
            'page_title': 'Checkout (Simulated)',
            'test_mode': True,
            'simulate': True,
            'razorpay_method': razorpay_method,
            'food_order': fo,
        }
        messages.info(request, 'Running Razorpay in simulated mode (no external requests).')
        return render(request, 'payments/razorpay_checkout.html', context)

    if client is None:
        # Test mode path when keys are not configured or invalid
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', '') or ''
        razorpay_order = {
            'id': f'test_order_{payment.pk}',
            'amount': int(payment.total_amount * 100),
        }
        payment.razorpay_order_id = razorpay_order['id']
        payment.save()

        # Map our payment method to Razorpay method (if selected)
        razorpay_method = None
        if payment.payment_method:
            method_map = {
                'credit_card': 'card',
                'debit_card': 'card',
                'upi': 'upi',
                'net_banking': 'netbanking',
                'wallet': 'wallet',
            }
            razorpay_method = method_map.get(payment.payment_method.name)

        fo = None
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
            except Exception:
                fo = None

        context = {
            'payment': payment,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': key_id,
            'page_title': 'Checkout (Test Mode)',
            'test_mode': True,
            'razorpay_method': razorpay_method,
            'food_order': fo,
        }
        messages.warning(request, 'Razorpay API keys are not configured or invalid. Running in test mode — no real payment will be processed.')
        return render(request, 'payments/razorpay_checkout.html', context)

    # Real client: create Razorpay order
    try:
        # Prepare notes for the Razorpay order. Support payments tied to bookings
        # and payments created for other order types (food orders stored in payment_notes).
        notes = {'user_id': request.user.id}
        if payment.booking:
            notes['booking_id'] = payment.booking.booking_id
        else:
            # Include food_order reference if present
            if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
                notes['food_order_id'] = payment.payment_notes.split(':', 1)[1]

        razorpay_order = client.order.create({
            'amount': int(payment.total_amount * 100),  # Amount in paise
            'currency': payment.currency,
            'receipt': payment.payment_id,
            'notes': notes
        })

        payment.razorpay_order_id = razorpay_order['id']
        payment.save()

        # Map our payment method to Razorpay method (if selected)
        razorpay_method = None
        if payment.payment_method:
            method_map = {
                'credit_card': 'card',
                'debit_card': 'card',
                'upi': 'upi',
                'net_banking': 'netbanking',
                'wallet': 'wallet',
            }
            razorpay_method = method_map.get(payment.payment_method.name)

        fo = None
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
            except Exception:
                fo = None

        context = {
            'payment': payment,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
            'page_title': 'Checkout',
            'razorpay_method': razorpay_method,
            'food_order': fo,
        }
        return render(request, 'payments/razorpay_checkout.html', context)

    except Exception as e:
        # AuthenticationError or other client errors bubble here.
        err_str = str(e) or ''
        logging.exception('Razorpay order creation failed')

        # If it's an authentication/network issue, fall back to simulated checkout
        if 'authentication' in err_str.lower() or '401' in err_str or 'unauthorized' in err_str.lower() or 'failed to resolve' in err_str.lower():
            # Create a simulated order so user can complete checkout locally
            key_id = getattr(settings, 'RAZORPAY_KEY_ID', '') or ''
            razorpay_order = {
                'id': f'fallback_order_{payment.pk}',
                'amount': int(payment.total_amount * 100),
            }
            payment.razorpay_order_id = razorpay_order['id']
            payment.save()

            # Map our payment method to Razorpay method (if selected)
            razorpay_method = None
            if payment.payment_method:
                method_map = {
                    'credit_card': 'card',
                    'debit_card': 'card',
                    'upi': 'upi',
                    'net_banking': 'netbanking',
                    'wallet': 'wallet',
                }
                razorpay_method = method_map.get(payment.payment_method.name)

            fo = None
            if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
                try:
                    fo_id = int(payment.payment_notes.split(':', 1)[1])
                    fo = FoodOrder.objects.filter(pk=fo_id).first()
                except Exception:
                    fo = None

            context = {
                'payment': payment,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key': key_id,
                'page_title': 'Checkout (Fallback - Auth Failed)',
                'test_mode': True,
                'simulate': True,
                'razorpay_method': razorpay_method,
                'food_order': fo,
            }
            messages.warning(request, 'Razorpay authentication failed — falling back to simulated checkout. Please verify your RAZORPAY_KEY_ID/SECRET in .env to enable real payments.')
            return render(request, 'payments/razorpay_checkout.html', context)

        # For other errors, show actionable feedback and redirect back
        messages.error(request, f'Error initializing payment with Razorpay: {err_str}')
        if payment.booking:
            return redirect('payments:payment_gateway', booking_id=payment.booking.pk)
        # try to send user to food order detail
        try:
            if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                return redirect('food:order_detail', pk=fo_id)
        except Exception:
            pass
        return redirect('food:order_list')


@csrf_exempt
@require_POST
def razorpay_callback(request):
    """
    Handle Razorpay payment callback
    """
    try:
        payment_id = request.POST.get('payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        # Try to locate the payment record by razorpay_order_id first,
        # fall back to the local payment_id if provided.
        payment = None
        if razorpay_order_id:
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            except Payment.DoesNotExist:
                payment = None

        if not payment and payment_id:
            try:
                payment = Payment.objects.get(pk=payment_id)
            except Payment.DoesNotExist:
                payment = None

        if not payment:
            # Nothing we can do without a payment record
            return JsonResponse({'status': 'error', 'message': 'Payment record not found'}, status=404)
        
        # Simulation path: test_order_/sim_order_ or global simulation enabled
        sim_enabled = is_simulation_enabled()
        if (razorpay_order_id and (str(razorpay_order_id).startswith('test_order_') or str(razorpay_order_id).startswith('sim_order_'))) or sim_enabled:
            import uuid
            # Ensure we have a payment id
            payment.razorpay_payment_id = razorpay_payment_id or f"SIMPAY{uuid.uuid4().hex[:8].upper()}"

            # Attempt to compute a realistic signature if secret available, else use placeholder
            key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '') or ''
            if razorpay_signature:
                sig = razorpay_signature
            elif key_secret:
                sig = compute_signature(razorpay_order_id, payment.razorpay_payment_id, key_secret)
            else:
                sig = 'SIMULATED_SIGNATURE'

            payment.razorpay_signature = sig
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.save()

            # Update related record: booking (for tickets) or food order
            if payment.booking:
                booking = payment.booking
                booking.status = 'confirmed'
                booking.payment_method = payment.payment_method.get_name_display() if payment.payment_method else 'online'
                booking.save()
            else:
                # Try to update a food order if referenced
                try:
                    if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
                        fo_id = int(payment.payment_notes.split(':', 1)[1])
                        food_order = FoodOrder.objects.filter(pk=fo_id, user=request.user).first()
                        if food_order:
                            food_order.status = 'preparing'
                            food_order.save()
                except Exception:
                    pass
            
            # Return JSON with redirect URL so client JS can navigate the main window
            success_url = reverse('payments:payment_success', kwargs={'payment_id': payment.pk})
            messages.success(request, 'Payment completed (simulated).')
            return JsonResponse({'status': 'success', 'redirect_url': success_url})

        # Verify Razorpay signature for real orders using validated client
        client = get_razorpay_client()
        if client is None:
            messages.error(request, 'Razorpay API keys are not properly configured.')
            payment.status = 'failed'
            payment.save()
            return JsonResponse({'status': 'error', 'message': 'Razorpay keys not configured'}, status=500)

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        # This will raise SignatureVerificationError if verification fails
        client.utility.verify_payment_signature(params_dict)
        
        # Payment verified
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.save()

        # Update related record: booking (for tickets) or food order
        if payment.booking:
            booking = payment.booking
            booking.status = 'confirmed'
            booking.payment_method = payment.payment_method.get_name_display() if payment.payment_method else 'online'
            booking.save()
        else:
            try:
                if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
                    fo_id = int(payment.payment_notes.split(':', 1)[1])
                    food_order = FoodOrder.objects.filter(pk=fo_id, user=request.user).first()
                    if food_order:
                        food_order.status = 'preparing'
                        food_order.save()
            except Exception:
                pass

        success_url = reverse('payments:payment_success', kwargs={'payment_id': payment.pk})
        messages.success(request, 'Payment completed successfully.')
        return JsonResponse({'status': 'success', 'redirect_url': success_url})
    
    except SignatureVerificationError:
        messages.error(request, 'Payment verification failed: Invalid signature.')
        try:
            payment.status = 'failed'
            payment.save()
        except:
            pass
        return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)
    except Payment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Payment record not found'}, status=404)
    except Exception as e:
        messages.error(request, f'Payment processing error: {str(e)}')
        try:
            payment.status = 'failed'
            payment.save()
        except:
            pass
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url='users:login')
def payment_success(request, payment_id):
    """
    Display payment success message
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    # Authorize access: payment either linked to a booking owned by user or linked to a food order in notes
    if payment.booking:
        if payment.booking.user != request.user:
            return HttpResponseForbidden()
    else:
        # check food order ownership
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
                if not fo or fo.user != request.user:
                    return HttpResponseForbidden()
            except Exception:
                return HttpResponseForbidden()
        else:
            return HttpResponseForbidden()
    
    # include food_order in context when payment references one
    fo = None
    if not payment.booking and payment.payment_notes and payment.payment_notes.startswith('food_order:'):
        try:
            fo_id = int(payment.payment_notes.split(':', 1)[1])
            fo = FoodOrder.objects.filter(pk=fo_id).first()
        except Exception:
            fo = None

    context = {
        'payment': payment,
        'food_order': fo,
        'page_title': 'Payment Successful',
    }
    return render(request, 'payments/payment_success.html', context)


@login_required(login_url='users:login')
def payment_failed(request, payment_id):
    """
    Display payment failed message and option to retry
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    if payment.booking:
        if payment.booking.user != request.user:
            return HttpResponseForbidden()
    else:
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
                if not fo or fo.user != request.user:
                    return HttpResponseForbidden()
            except Exception:
                return HttpResponseForbidden()
        else:
            return HttpResponseForbidden()
    
    context = {
        'payment': payment,
        'food_order': None,
        'page_title': 'Payment Failed',
    }

    # If payment refers to a food order, include it
    if not payment.booking and payment.payment_notes and payment.payment_notes.startswith('food_order:'):
        try:
            fo_id = int(payment.payment_notes.split(':', 1)[1])
            context['food_order'] = FoodOrder.objects.filter(pk=fo_id).first()
        except Exception:
            context['food_order'] = None

    return render(request, 'payments/payment_failed.html', context)


@login_required(login_url='users:login')
def retry_payment(request, payment_id):
    """
    Retry a failed payment by resetting payment status and redirecting to checkout
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    if payment.booking:
        if payment.booking.user != request.user:
            return HttpResponseForbidden()
    else:
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
                if not fo or fo.user != request.user:
                    return HttpResponseForbidden()
            except Exception:
                return HttpResponseForbidden()
        else:
            return HttpResponseForbidden()
    
    # Only allow retry for failed payments
    if payment.status not in ['failed', 'pending']:
        messages.warning(request, 'This payment cannot be retried.')
        if payment.booking:
            return redirect('bookings:booking_detail', pk=payment.booking.pk)
        # fallback to food orders list
        return redirect('food:order_list')
    
    # Reset payment status to allow re-attempt
    payment.status = 'pending'
    payment.razorpay_payment_id = None
    payment.razorpay_signature = None
    payment.razorpay_order_id = None
    payment.completed_at = None
    payment.save()
    
    messages.info(request, f'Retrying payment of ₹{payment.total_amount}...')
    return redirect('payments:razorpay_checkout', payment_id=payment.pk)


@login_required(login_url='users:login')
def simulate_payment(request, payment_id):
    """
    Debug-only: simulate successful payment for a payment record (marks completed)
    """
    # Only allow simulation in DEBUG mode
    if not getattr(settings, 'DEBUG', False):
        return HttpResponseForbidden('Simulation not allowed in production')

    payment = get_object_or_404(Payment, pk=payment_id)
    if payment.booking:
        if payment.booking.user != request.user:
            return HttpResponseForbidden()
    else:
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
                if not fo or fo.user != request.user:
                    return HttpResponseForbidden()
            except Exception:
                return HttpResponseForbidden()
        else:
            return HttpResponseForbidden()

    # Mark payment as completed
    payment.razorpay_payment_id = f"SIMPAY{uuid.uuid4().hex[:8].upper()}"
    payment.razorpay_signature = 'SIMULATED_SIGNATURE'
    payment.status = 'completed'
    payment.completed_at = timezone.now()
    payment.save()

    # Update related record
    if payment.booking:
        booking = payment.booking
        booking.status = 'confirmed'
        booking.payment_method = payment.payment_method.get_name_display() if payment.payment_method else 'online'
        booking.save()
    else:
        try:
            if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                food_order = FoodOrder.objects.filter(pk=fo_id, user=request.user).first()
                if food_order:
                    food_order.status = 'preparing'
                    food_order.save()
        except Exception:
            pass

    messages.success(request, f'Payment of ₹{payment.total_amount} simulated as successful.')
    return redirect('payments:payment_success', payment_id=payment.pk)


@login_required(login_url='users:login')
def invoice_view(request, payment_id):
    """
    Display and download invoice
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    if payment.booking:
        if payment.booking.user != request.user:
            return HttpResponseForbidden()
    else:
        if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
            try:
                fo_id = int(payment.payment_notes.split(':', 1)[1])
                fo = FoodOrder.objects.filter(pk=fo_id).first()
                if not fo or fo.user != request.user:
                    return HttpResponseForbidden()
            except Exception:
                return HttpResponseForbidden()
        else:
            return HttpResponseForbidden()
    
    try:
        invoice = Invoice.objects.get(payment=payment)
    except Invoice.DoesNotExist:
        # Create an invoice automatically from the payment record
        try:
            # Derive amounts: prefer using payment fields
            subtotal = getattr(payment, 'amount', 0) or 0
            tax = getattr(payment, 'processing_charges', 0) or 0
            total = getattr(payment, 'total_amount', subtotal + tax) or (subtotal + tax)

            due_date = timezone.now().date() + timedelta(days=7)
            invoice = Invoice.objects.create(
                payment=payment,
                due_date=due_date,
                subtotal=subtotal,
                tax=tax,
                total=total,
                is_paid=(payment.status == 'completed')
            )
            messages.success(request, 'Invoice generated successfully.')
        except Exception as e:
            messages.error(request, f'Invoice not available and automatic generation failed: {e}')
            # redirect to appropriate place depending on related record
            if payment.booking:
                return redirect('bookings:booking_detail', pk=payment.booking.pk)
            try:
                if payment.payment_notes and payment.payment_notes.startswith('food_order:'):
                    fo_id = int(payment.payment_notes.split(':', 1)[1])
                    return redirect('food:order_detail', pk=fo_id)
            except Exception:
                pass
            return redirect('food:order_list')
    
    context = {
        'payment': payment,
        'invoice': invoice,
        'food_order': None,
        'page_title': f'Invoice #{invoice.invoice_id}',
    }
    if not payment.booking and payment.payment_notes and payment.payment_notes.startswith('food_order:'):
        try:
            fo_id = int(payment.payment_notes.split(':', 1)[1])
            context['food_order'] = FoodOrder.objects.filter(pk=fo_id).first()
        except Exception:
            context['food_order'] = None
    # If this payment is linked to a booking, include booking/ticket details
    if payment.booking:
        booking = payment.booking
        context['booking'] = booking
        # include tickets if available; normalize to a queryset/list so template can iterate
        tickets = None
        # Prefer explicit related name 'tickets' if available
        if hasattr(booking, 'tickets'):
            try:
                tickets = booking.tickets.all()
            except Exception:
                tickets = None

        # Fallback to reverse relation 'ticket_set'
        if tickets is None:
            try:
                tickets = booking.ticket_set.all()
            except Exception:
                tickets = []

        # Ensure tickets is an iterable (QuerySet or list)
        try:
            # If it's a RelatedManager or similar, call .all()
            if hasattr(tickets, 'all') and not hasattr(tickets, '__iter__'):
                tickets = tickets.all()
        except Exception:
            # As a last resort, coerce to list
            try:
                tickets = list(tickets)
            except Exception:
                tickets = []

        context['tickets'] = tickets

    # Mark whether this render is for download (so template can hide interactive actions)
    is_download = (request.GET.get('download') == '1')
    context['is_download'] = is_download

    # Build a usable logo URL or inline data URI so the logo appears in downloaded files/PDFs
    try:
        logo_rel = static('img/logo.png')
        logo_url = request.build_absolute_uri(logo_rel)
    except Exception:
        logo_url = None
    context['logo_url'] = logo_url

    # Try to find a static file on disk and embed it as base64 (best for PDF embedding)
    logo_data = None
    try:
        candidates = []
        if getattr(settings, 'STATIC_ROOT', None):
            candidates.append(os.path.join(settings.STATIC_ROOT, 'img', 'logo.png'))
        if getattr(settings, 'STATICFILES_DIRS', None):
            for d in settings.STATICFILES_DIRS:
                candidates.append(os.path.join(d, 'img', 'logo.png'))
        # Also look relative to project 'static/img/logo.png'
        proj_static = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png') if getattr(settings, 'BASE_DIR', None) else None
        if proj_static:
            candidates.append(proj_static)

        found = None
        for c in candidates:
            if c and os.path.exists(c):
                found = c
                break
        if found:
            with open(found, 'rb') as f:
                b = f.read()
            logo_data = 'data:image/png;base64,' + base64.b64encode(b).decode('ascii')
        else:
            # Fallback: small SVG brand mark embedded as data URI (portable for HTML/PDF)
            svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="60"><rect rx="8" width="100%" height="100%" fill="#00C2FF"/><text x="20" y="38" font-family="Arial, Helvetica, sans-serif" font-size="22" fill="white">CineBook</text></svg>'''
            logo_data = 'data:image/svg+xml;utf8,' + urllib.parse.quote(svg)
    except Exception:
        logo_data = None

    context['logo_data'] = logo_data

    # Support direct download as an HTML attachment (works without extra libraries)
    if is_download:
        html = render_to_string('payments/invoice.html', context=context, request=request)
        filename = f"invoice_{invoice.invoice_id}.html"
        response = HttpResponse(html, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return render(request, 'payments/invoice.html', context)
