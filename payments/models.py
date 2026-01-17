"""
Payments App Models
- Payment: Process and track payments for bookings
- Refund: Handle refunds for cancelled bookings
- PaymentMethod: Support multiple payment methods
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class PaymentMethod(models.Model):
    """
    Supported payment methods
    """
    METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
        ('wallet', 'Digital Wallet'),
    ]
    
    name = models.CharField(max_length=50, choices=METHOD_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    charges = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Processing charges
    
    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
    
    def __str__(self):
        return self.get_name_display()


class Payment(models.Model):
    """
    Payment records for bookings
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    payment_id = models.CharField(max_length=20, unique=True, editable=False)
    # Allow payments that are not tied to a Booking (e.g. food orders)
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='payment', null=True, blank=True)
    
    # Amount details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    processing_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Payment details
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Razorpay integration
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Additional info
    currency = models.CharField(max_length=3, default='INR')
    payment_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        if self.booking:
            return f"Payment #{self.payment_id} - {self.booking.booking_id}"
        return f"Payment #{self.payment_id} - (no booking)"
    
    def save(self, *args, **kwargs):
        """Generate unique payment ID"""
        if not self.payment_id:
            import uuid
            self.payment_id = f"PAY{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class Refund(models.Model):
    """
    Refunds for cancelled bookings
    """
    REFUND_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    refund_id = models.CharField(max_length=20, unique=True, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='refund')
    booking_cancellation = models.OneToOneField('bookings.BookingCancellation', on_delete=models.CASCADE, related_name='refund')
    
    # Refund details
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    refund_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_refund_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Status
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    reason = models.TextField()
    
    # Razorpay integration
    razorpay_refund_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund #{self.refund_id} - {self.booking_cancellation.booking.booking_id}"
    
    def save(self, *args, **kwargs):
        """Generate unique refund ID"""
        if not self.refund_id:
            import uuid
            self.refund_id = f"REF{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """
    Invoice generation for payments
    """
    invoice_id = models.CharField(max_length=20, unique=True, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    
    # Invoice details
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    # Items
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    is_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
    
    def __str__(self):
        return f"Invoice #{self.invoice_id}"
    
    def save(self, *args, **kwargs):
        """Generate unique invoice ID"""
        if not self.invoice_id:
            import uuid
            self.invoice_id = f"INV{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

