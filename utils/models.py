"""
Utility functions for the application
- QR code generation
- PDF generation for tickets
- Email sending
- SMS notifications
"""

import qrcode
from io import BytesIO
from django.core.files import File
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
import os


def generate_qr_code(data):
    """
    Generate QR code for tickets
    
    Args:
        data: String data to encode in QR code
    
    Returns:
        File object with QR code image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO object
    file_path = BytesIO()
    img.save(file_path, format='PNG')
    file_path.seek(0)
    
    return File(file_path, name=f'qr_{data}.png')


def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email to user
    
    Args:
        booking: Booking object
    """
    context = {
        'booking': booking,
        'user': booking.user,
        'tickets': booking.tickets.all(),
    }
    
    html_message = render_to_string('emails/booking_confirmation.html', context)
    
    send_mail(
        subject=f'Booking Confirmation - {booking.booking_id}',
        message=f'Your booking {booking.booking_id} has been confirmed.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_payment_confirmation_email(payment):
    """
    Send payment confirmation email
    
    Args:
        payment: Payment object
    """
    context = {
        'payment': payment,
        'booking': payment.booking,
        'user': payment.booking.user,
    }
    
    html_message = render_to_string('emails/payment_confirmation.html', context)
    
    send_mail(
        subject=f'Payment Confirmation - {payment.payment_id}',
        message=f'Your payment {payment.payment_id} has been confirmed.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[payment.booking.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_cancellation_email(booking, cancellation):
    """
    Send booking cancellation and refund email
    
    Args:
        booking: Booking object
        cancellation: BookingCancellation object
    """
    context = {
        'booking': booking,
        'cancellation': cancellation,
        'user': booking.user,
    }
    
    html_message = render_to_string('emails/cancellation.html', context)
    
    send_mail(
        subject=f'Booking Cancelled - {booking.booking_id}',
        message=f'Your booking {booking.booking_id} has been cancelled.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_food_order_confirmation_email(food_order):
    """
    Send food order confirmation email
    
    Args:
        food_order: FoodOrder object
    """
    context = {
        'food_order': food_order,
        'user': food_order.user,
        'items': food_order.items.all(),
    }
    
    html_message = render_to_string('emails/food_order_confirmation.html', context)
    
    send_mail(
        subject=f'Food Order Confirmed - {food_order.order_id}',
        message=f'Your food order {food_order.order_id} has been confirmed.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[food_order.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_food_order_ready_notification(food_order):
    """
    Send notification when food order is ready
    
    Args:
        food_order: FoodOrder object
    """
    context = {
        'food_order': food_order,
        'user': food_order.user,
    }
    
    html_message = render_to_string('emails/food_ready.html', context)
    
    send_mail(
        subject=f'Food Order Ready - {food_order.order_id}',
        message=f'Your food order {food_order.order_id} is ready for pickup.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[food_order.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def calculate_tax(amount, tax_percentage=5):
    """
    Calculate tax on amount
    
    Args:
        amount: Base amount
        tax_percentage: Tax percentage (default 5%)
    
    Returns:
        Tax amount
    """
    return (amount * tax_percentage) / 100


def calculate_final_price(base_price, tax_amount=0, discount=0):
    """
    Calculate final price
    
    Args:
        base_price: Base price
        tax_amount: Tax to add
        discount: Discount to subtract
    
    Returns:
        Final price
    """
    return base_price + tax_amount - discount


def format_currency(amount):
    """
    Format amount as currency
    
    Args:
        amount: Numeric amount
    
    Returns:
        Formatted currency string
    """
    return f"₹{amount:,.2f}"


def get_seat_label(row, seat_number):
    """
    Generate seat label (e.g., A1, A2, B1, etc.)
    
    Args:
        row: Seat row (A, B, C, etc.)
        seat_number: Seat number (1, 2, 3, etc.)
    
    Returns:
        Formatted seat label
    """
    return f"{row}{seat_number}"


def check_show_availability(show):
    """
    Check if a show has available seats
    
    Args:
        show: Show object
    
    Returns:
        Boolean indicating availability
    """
    from bookings.models import Ticket
    from theatres.models import Seat
    
    booked_count = Ticket.objects.filter(show=show).count()
    total_seats = Seat.objects.filter(screen=show.screen).count()
    
    return booked_count < total_seats


def get_available_seat_count(show):
    """
    Get count of available seats for a show
    
    Args:
        show: Show object
    
    Returns:
        Number of available seats
    """
    from bookings.models import Ticket
    from theatres.models import Seat
    
    booked_count = Ticket.objects.filter(show=show).count()
    total_seats = Seat.objects.filter(screen=show.screen, is_available=True).count()
    
    return total_seats - booked_count


def get_occupied_seats(show):
    """
    Get list of occupied seat IDs for a show
    
    Args:
        show: Show object
    
    Returns:
        List of seat IDs
    """
    from bookings.models import Ticket
    
    return list(Ticket.objects.filter(show=show).values_list('seat_id', flat=True))
