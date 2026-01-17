"""
Views for Utils app (API endpoints)
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from theatres.models import Show, Seat
from bookings.models import Ticket
from .forms import ContactForm

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def get_available_seats_api(request, show_id):
    """
    API endpoint to get available seats for a show
    Returns JSON with seat information
    """
    try:
        show = Show.objects.get(id=show_id)
        booked_seat_ids = Ticket.objects.filter(show=show).values_list('seat_id', flat=True)
        available_seats = show.screen.seats.filter(is_available=True).exclude(id__in=booked_seat_ids)
        
        seats_data = []
        for seat in available_seats:
            seats_data.append({
                'id': seat.id,
                'row': seat.row,
                'seat_number': seat.seat_number,
                'type': seat.seat_type,
                'price': float(seat.base_price),
            })
        
        return JsonResponse({
            'status': 'success',
            'seats': seats_data,
            'total_available': len(seats_data),
        })
    except Show.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Show not found'
        }, status=404)


@require_http_methods(["GET"])
def get_seat_status_api(request, show_id):
    """
    API endpoint to get real-time seat status for a show
    """
    try:
        show = Show.objects.get(id=show_id)
        booked_seat_ids = list(Ticket.objects.filter(show=show).values_list('seat_id', flat=True))
        
        seats = show.screen.seats.all()
        seat_status = {}
        
        for seat in seats:
            seat_key = f"{seat.row}{seat.seat_number}"
            seat_status[seat_key] = {
                'id': seat.id,
                'booked': seat.id in booked_seat_ids,
                'type': seat.seat_type,
                'price': float(seat.base_price),
            }
        
        return JsonResponse({
            'status': 'success',
            'seats': seat_status,
        })
    except Show.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Show not found'
        }, status=404)


@require_http_methods(["GET", "POST"])
def contact(request):
    """
    Contact form view
    Sends an email to the contact email specified in the template
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            email = form.cleaned_data.get('email')
            message = form.cleaned_data.get('message')
            
            # Email to admin/contact email from settings
            contact_email = settings.CONTACT_EMAIL
            
            # Send email to admin
            subject = f'New Contact Form Submission from {name}'
            body = f"""
You have received a new contact form submission:

Name: {name}
Email: {email}
Message:
{message}

---
Please reply to the user at: {email}
            """
            
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@cinebook.com',
                    recipient_list=[contact_email],
                    fail_silently=False,
                )
                
                # Optional: Send confirmation email to user
                user_subject = 'We received your message - CineBook'
                user_body = f"""
Dear {name},

Thank you for contacting CineBook. We have received your message and will get back to you as soon as possible.

Best regards,
CineBook Team
                """
                
                send_mail(
                    subject=user_subject,
                    message=user_body,
                    from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@cinebook.com',
                    recipient_list=[email],
                    fail_silently=True,  # Don't fail if user email fails
                )
                
                messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
                logger.info(f'Contact form submitted by {email} - Message to {contact_email}')
                return redirect('contact')
            except Exception as e:
                error_msg = str(e)
                logger.error(f'Failed to send contact email: {error_msg}')
                
                # Provide helpful error message
                if 'Authentication' in error_msg or '530' in error_msg:
                    messages.error(request, 'Email configuration error. Please contact the administrator. (Auth error)')
                else:
                    messages.error(request, f'Error sending message: {error_msg}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    context = {
        'form': form,
        'page_title': 'Contact Us'
    }
    return render(request, 'contact.html', context)
