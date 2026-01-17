"""
Admin configuration for Payments app
"""

from django.contrib import admin
from .models import PaymentMethod, Payment, Refund, Invoice


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin for PaymentMethod"""
    list_display = ['name', 'is_active', 'charges']
    list_filter = ['is_active']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment"""
    list_display = ['payment_id', 'booking', 'amount', 'total_amount', 'status', 'payment_method', 'created_at']
    search_fields = ['payment_id', 'booking__booking_id', 'razorpay_payment_id']
    list_filter = ['status', 'payment_method', 'created_at']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'completed_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'booking', 'status', 'payment_method')
        }),
        ('Amount Details', {
            'fields': ('amount', 'processing_charges', 'total_amount', 'currency')
        }),
        ('Razorpay Integration', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Admin for Refund"""
    list_display = ['refund_id', 'payment', 'refund_amount', 'net_refund_amount', 'status', 'created_at']
    search_fields = ['refund_id', 'payment__payment_id']
    list_filter = ['status', 'created_at']
    readonly_fields = ['refund_id', 'created_at', 'processed_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin for Invoice"""
    list_display = ['invoice_id', 'payment', 'invoice_date', 'total', 'is_paid']
    search_fields = ['invoice_id', 'payment__payment_id']
    list_filter = ['is_paid', 'invoice_date']
    readonly_fields = ['invoice_id', 'created_at', 'updated_at']
