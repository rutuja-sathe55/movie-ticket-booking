"""
Views for Food app
- Display menu items
- Create and manage food orders
- Track order status
- Submit reviews
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Avg, Sum
from decimal import Decimal
from .models import FoodCategory, FoodItem, FoodOrder, FoodOrderItem, FoodReview
from .forms import FoodOrderForm, FoodOrderItemForm, FoodReviewForm
from theatres.models import Theatre
from bookings.models import Booking
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from payments.models import Payment


def menu(request, theatre_id=None):
    """
    Display food menu items organized by category
    """
    categories = FoodCategory.objects.all()
    food_items = FoodItem.objects.filter(is_available=True).prefetch_related('category')
    
    # Filter by category if specified
    if request.GET.get('category'):
        category_id = request.GET.get('category')
        food_items = food_items.filter(category_id=category_id)
    
    # Add average rating
    food_items = food_items.annotate(avg_rating=Avg('reviews__rating'))
    
    context = {
        'categories': categories,
        'food_items': food_items,
        'theatre_id': theatre_id,
        'page_title': 'Food & Beverages',
    }
    return render(request, 'food/menu.html', context)


def food_detail(request, pk):
    """
    Display detailed information about a food item with reviews
    """
    food_item = get_object_or_404(FoodItem, pk=pk)
    reviews = food_item.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    context = {
        'food_item': food_item,
        'reviews': reviews,
        'average_rating': round(avg_rating, 1),
        'user_review': user_review,
        'page_title': food_item.name,
    }
    return render(request, 'food/food_detail.html', context)


@login_required(login_url='users:login')
@require_http_methods(["GET", "POST"])
def create_food_order(request, booking_id=None):
    """
    Create a new food order
    """
    booking = None
    theatre = None
    
    if booking_id:
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        theatre = booking.show.screen.theatre
    elif request.GET.get('theatre_id'):
        theatre = get_object_or_404(Theatre, pk=request.GET.get('theatre_id'))
    
    if request.method == 'POST':
        form = FoodOrderForm(request.POST)
        if form.is_valid():
            food_order = form.save(commit=False)
            food_order.user = request.user
            food_order.theatre = theatre or Theatre.objects.first()
            food_order.booking = booking
            
            # Get items from POST
            items_data = request.POST.getlist('items')
            total_amount = 0
            tax = 0
            
            if not items_data:
                messages.error(request, 'Please select at least one item.')
            else:
                food_order.save()
                
                # Create order items
                for item_id in items_data:
                    try:
                        item = FoodItem.objects.get(id=item_id)
                        quantity = int(request.POST.get(f'quantity_{item_id}', 1))
                        
                        item_total = item.price * quantity
                        FoodOrderItem.objects.create(
                            food_order=food_order,
                            food_item=item,
                            quantity=quantity,
                            unit_price=item.price,
                            total_price=item_total
                        )
                        total_amount += item_total
                    except (FoodItem.DoesNotExist, ValueError):
                        continue
                
                tax = total_amount * 0.05  # 5% tax
                food_order.total_amount = total_amount
                food_order.tax = tax
                food_order.final_amount = total_amount + tax
                food_order.save()
                
                messages.success(request, f'Food order created! Order ID: {food_order.order_id}')
                return redirect('food:order_detail', pk=food_order.pk)
        else:
            messages.error(request, 'Error creating order.')
    else:
        form = FoodOrderForm()
    
    context = {
        'form': form,
        'booking': booking,
        'theatre': theatre,
        'page_title': 'Order Food & Beverages',
    }
    return render(request, 'food/create_order.html', context)


@login_required(login_url='users:login')
def food_order_detail(request, pk):
    """
    Display food order details
    """
    food_order = get_object_or_404(FoodOrder, pk=pk, user=request.user)
    items = food_order.items.all()
    
    context = {
        'food_order': food_order,
        'items': items,
        'page_title': f'Food Order - {food_order.order_id}',
    }
    return render(request, 'food/order_detail.html', context)


@login_required(login_url='users:login')
def cancel_food_order(request, pk):
    """Allow a user to cancel their food order if it's not already delivered/cancelled."""
    food_order = get_object_or_404(FoodOrder, pk=pk, user=request.user)

    # Only allow cancel for certain statuses
    if food_order.status in ['delivered', 'cancelled', 'ready']:
        messages.error(request, 'This order cannot be cancelled at this stage.')
        return redirect('food:order_detail', pk=food_order.pk)

    if request.method == 'POST':
        # mark as cancelled
        food_order.status = 'cancelled'
        food_order.save()

        # If there is a payment associated, mark as cancelled too
        try:
            payment = Payment.objects.filter(payment_notes__startswith=f'food_order:{food_order.pk}').first()
            if payment:
                payment.status = 'cancelled'
                payment.save()
        except Exception:
            pass

        messages.success(request, 'Your food order has been cancelled.')
        return redirect('food:order_list')

    # GET -> render confirmation
    context = {
        'food_order': food_order,
        'page_title': f'Cancel Order - {food_order.order_id}',
    }
    return render(request, 'food/cancel_order.html', context)


@login_required(login_url='users:login')
def food_order_list(request):
    """
    Display all food orders for the logged-in user
    """
    food_orders = FoodOrder.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'food_orders': food_orders,
        'page_title': 'My Food Orders',
    }
    return render(request, 'food/order_list.html', context)


@login_required(login_url='users:login')
@require_http_methods(["GET", "POST"])
def submit_food_review(request, food_id):
    """
    Submit or update a review for a food item
    """
    food_item = get_object_or_404(FoodItem, pk=food_id)
    
    try:
        existing_review = FoodReview.objects.get(food_item=food_item, user=request.user)
        is_update = True
    except FoodReview.DoesNotExist:
        existing_review = None
        is_update = False
    
    if request.method == 'POST':
        form = FoodReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.food_item = food_item
            review.user = request.user
            review.save()
            
            action = 'Updated' if is_update else 'Added'
            messages.success(request, f'{action} your review successfully!')
            return redirect('food:food_detail', pk=food_id)
        else:
            messages.error(request, 'Error submitting review.')
    else:
        form = FoodReviewForm(instance=existing_review)
    
    context = {
        'form': form,
        'food_item': food_item,
        'is_update': is_update,
        'page_title': f'Review - {food_item.name}',
    }
    return render(request, 'food/submit_review.html', context)


# ============================================================================
# SHOPPING CART MANAGEMENT
# ============================================================================

def get_cart_from_session(request):
    """
    Get food cart from session
    Returns cart dict with structure: {food_id: {quantity, special_instructions}, ...}
    """
    if 'food_cart' not in request.session:
        request.session['food_cart'] = {}
    return request.session['food_cart']


def save_cart_to_session(request, cart):
    """Save food cart to session"""
    request.session['food_cart'] = cart
    request.session.modified = True


@require_http_methods(["POST"])
@login_required(login_url='users:login')
def add_to_cart(request, food_id):
    """
    Add food item to cart with quantity and special instructions
    """
    try:
        food_item = get_object_or_404(FoodItem, pk=food_id)
        quantity = int(request.POST.get('quantity', 1))
        special_instructions = request.POST.get('special_instructions', '').strip()
        
        if quantity < 1:
            messages.error(request, 'Quantity must be at least 1')
            return redirect('food:food_detail', pk=food_id)
        
        if quantity > food_item.available_quantity:
            messages.error(request, f'Only {food_item.available_quantity} items available')
            return redirect('food:food_detail', pk=food_id)
        
        cart = get_cart_from_session(request)
        
        if str(food_id) in cart:
            # Update existing item
            cart[str(food_id)]['quantity'] += quantity
            cart[str(food_id)]['special_instructions'] = special_instructions
            messages.info(request, f'{food_item.name} quantity updated in cart')
        else:
            # Add new item
            cart[str(food_id)] = {
                'quantity': quantity,
                'special_instructions': special_instructions,
            }
            messages.success(request, f'{food_item.name} added to cart')
        
        save_cart_to_session(request, cart)
        return redirect('food:view_cart')
    
    except FoodItem.DoesNotExist:
        messages.error(request, 'Food item not found')
        return redirect('food:menu')
    except ValueError:
        messages.error(request, 'Invalid quantity')
        return redirect('food:food_detail', pk=food_id)


@login_required(login_url='users:login')
def view_cart(request):
    """
    Display shopping cart with all items and totals
    """
    cart = get_cart_from_session(request)
    cart_items = []
    subtotal = Decimal('0.00')
    
    for food_id, item_data in cart.items():
        try:
            food_item = FoodItem.objects.get(pk=int(food_id))
            quantity = item_data['quantity']
            special_instructions = item_data.get('special_instructions', '')
            
            total_price = Decimal(str(food_item.price)) * quantity
            subtotal += total_price
            
            cart_items.append({
                'pk': food_item.pk,
                'food_item': food_item,
                'quantity': quantity,
                'special_instructions': special_instructions,
                'total_price': total_price,
            })
        except (FoodItem.DoesNotExist, ValueError):
            # Remove invalid item from cart
            del cart[food_id]
            save_cart_to_session(request, cart)
    
    tax = subtotal * Decimal('0.05')  # 5% tax
    discount = Decimal('0.00')
    total = subtotal + tax - discount
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'discount': discount,
        'total': total,
        'page_title': 'Food Cart',
    }
    return render(request, 'food/cart.html', context)


@require_http_methods(["POST"])
@login_required(login_url='users:login')
def remove_from_cart(request, food_id):
    """
    Remove item from cart or update session cart item
    """
    cart = get_cart_from_session(request)
    
    if str(food_id) in cart:
        food_item = FoodItem.objects.filter(pk=int(food_id)).first()
        if food_item:
            messages.info(request, f'{food_item.name} removed from cart')
        del cart[str(food_id)]
        save_cart_to_session(request, cart)
    
    return redirect('food:view_cart')


@login_required(login_url='users:login')
def checkout(request):
    """
    Checkout page - prepare food order for payment
    """
    cart = get_cart_from_session(request)
    
    if not cart:
        messages.error(request, 'Your cart is empty')
        return redirect('food:menu')
    
    # Get all theatres
    theatres = Theatre.objects.all().order_by('city', 'name')
    if not theatres.exists():
        messages.error(request, 'No theatres available. Please contact support.')
        return redirect('food:view_cart')
    
    selected_theatre = theatres.first()
    
    # Calculate cart totals
    order_items = []
    subtotal = Decimal('0.00')
    
    for food_id, item_data in cart.items():
        try:
            food_item = FoodItem.objects.get(pk=int(food_id))
            quantity = item_data['quantity']
            special_instructions = item_data.get('special_instructions', '')
            
            total_price = Decimal(str(food_item.price)) * quantity
            subtotal += total_price
            
            order_items.append({
                'food_item': food_item,
                'quantity': quantity,
                'special_instructions': special_instructions,
                'total_price': total_price,
            })
        except (FoodItem.DoesNotExist, ValueError):
            continue
    
    if not order_items:
        messages.error(request, 'Invalid items in cart')
        return redirect('food:view_cart')
    
    tax = subtotal * Decimal('0.05')
    discount = Decimal('0.00')
    total = subtotal + tax - discount
    special_instructions = request.POST.get('special_instructions', '')
    
    if request.method == 'POST':
        try:
            # Get theatre selection
            theatre_id = request.POST.get('theatre_id')
            if not theatre_id:
                messages.error(request, 'Please select a theatre')
            else:
                theatre = get_object_or_404(Theatre, pk=theatre_id)
                
                # Create FoodOrder
                food_order = FoodOrder.objects.create(
                    user=request.user,
                    theatre=theatre,
                    total_amount=subtotal,
                    tax=tax,
                    discount=discount,
                    final_amount=total,
                    special_instructions=special_instructions,
                    status='pending'
                )
                
                # Create order items
                for item_data in order_items:
                    FoodOrderItem.objects.create(
                        food_order=food_order,
                        food_item=item_data['food_item'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['food_item'].price,
                        total_price=item_data['total_price'],
                        special_instructions=item_data['special_instructions'],
                    )
                
                # Clear cart
                save_cart_to_session(request, {})
                
                messages.success(request, f'Order created! Order ID: {food_order.order_id}')
                
                # Redirect to payment with food order ID
                return redirect('payments:initiate_payment', order_type='food', order_id=food_order.pk)
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
    
    context = {
        'order_items': order_items,
        'subtotal': subtotal,
        'tax': tax,
        'discount': discount,
        'total': total,
        'theatres': theatres,
        'selected_theatre': selected_theatre,
        'special_instructions': special_instructions,
        'page_title': 'Checkout - Food Order',
    }
    return render(request, 'food/checkout.html', context)
