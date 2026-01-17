"""
Bookings App Models
- Booking: Main booking record with multiple tickets
- Ticket: Individual ticket for a specific seat
- Generates QR code for tickets
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.conf import settings
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image


class Booking(models.Model):
    """
    Main booking record containing all tickets for a user
    """
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='bookings')
    show = models.ForeignKey('theatres.Show', on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Status tracking
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)  # Credit Card, Debit Card, UPI, etc.
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    booking_date = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['booking_id']),
        ]
    
    def __str__(self):
        return f"Booking #{self.booking_id} - {self.user.username}"
    
    def get_absolute_url(self):
        """Return the URL to access this booking's details"""
        return reverse('bookings:booking_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        """Generate unique booking ID if not exists"""
        if not self.booking_id:
            self.booking_id = f"BK{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_ticket_count(self):
        """Get total number of tickets in this booking"""
        return self.tickets.count()


class Ticket(models.Model):
    """
    Individual ticket for a specific seat in a booking
    """
    TICKET_STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),
    ]
    
    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='tickets')
    show = models.ForeignKey('theatres.Show', on_delete=models.CASCADE, related_name='tickets')
    seat = models.ForeignKey('theatres.Seat', on_delete=models.CASCADE, related_name='tickets')
    
    # Pricing
    base_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    final_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    
    # QR Code for entry
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_data = models.CharField(max_length=255, unique=True)  # Unique identifier for QR
    
    # Status
    status = models.CharField(max_length=20, choices=TICKET_STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        unique_together = ['show', 'seat']  # Can't have duplicate seat in same show
        ordering = ['created_at']
    
    def __str__(self):
        return f"Ticket #{self.ticket_id} - {self.seat}"
    
    def save(self, *args, **kwargs):
        """Generate ticket ID and QR code"""
        if not self.ticket_id:
            self.ticket_id = f"TK{uuid.uuid4().hex[:8].upper()}"
        
        # Only set qr_data if booking and seat are assigned
        if self.booking_id and self.seat_id and self.show_id and not self.qr_data:
            # Point to the ticket preview page so scanning shows ticket details
            # (Ticket ID, Movie, Show, Seat, Price, Booking ID) with download option.
            try:
                path = reverse('bookings:ticket_preview', kwargs={'ticket_id': self.ticket_id})
            except Exception:
                path = f"/bookings/ticket/{self.ticket_id}/preview/"

            site = getattr(settings, 'SITE_URL', '') or ''
            # Ensure site does not end with slash
            if site.endswith('/'):
                site = site[:-1]

            self.qr_data = f"{site}{path}" if site else path
        
        # Generate QR code before saving (to ensure we save once with all data)
        if not self.qr_code and self.booking_id and self.seat_id:
            self.qr_code = self.generate_qr_code()
        
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        """Generate QR code for the ticket"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO object
        file_name = f"qr_{self.ticket_id}.png"
        file_path = BytesIO()
        img.save(file_path)
        
        return File(file_path, name=file_name)


class BookingCancellation(models.Model):
    """
    Track cancelled bookings and refunds
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='cancellation')
    cancelled_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    cancellation_reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cancellation_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    cancelled_at = models.DateTimeField(auto_now_add=True)
    refund_processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Booking Cancellation"
        verbose_name_plural = "Booking Cancellations"
    
    def __str__(self):
        return f"Cancellation - {self.booking.booking_id}"
