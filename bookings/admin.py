"""
Admin configuration for Bookings app
"""

from django.contrib import admin
from .models import Booking, Ticket, BookingCancellation


class TicketInline(admin.TabularInline):
    """Inline admin for Tickets within Booking"""
    model = Ticket
    extra = 0
    readonly_fields = ['ticket_id', 'qr_data', 'created_at']
    fields = ['ticket_id', 'seat', 'base_price', 'tax', 'final_price', 'status']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin for Booking"""
    list_display = ['booking_id', 'user', 'show', 'total_amount', 'final_amount', 'status', 'created_at']
    search_fields = ['booking_id', 'user__username', 'show__movie__title']
    list_filter = ['status', 'created_at', 'payment_method']
    readonly_fields = ['booking_id', 'created_at', 'updated_at']
    inlines = [TicketInline]
    date_hierarchy = 'created_at'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin for Ticket"""
    list_display = ['ticket_id', 'booking', 'seat', 'show', 'final_price', 'status']
    search_fields = ['ticket_id', 'booking__booking_id', 'seat__row']
    list_filter = ['status', 'created_at']
    readonly_fields = ['ticket_id', 'qr_code', 'qr_data', 'created_at', 'updated_at']


@admin.register(BookingCancellation)
class BookingCancellationAdmin(admin.ModelAdmin):
    """Admin for BookingCancellation"""
    list_display = ['booking', 'cancelled_by', 'refund_amount', 'cancellation_charges', 'cancelled_at']
    search_fields = ['booking__booking_id']
    list_filter = ['cancelled_at']
    readonly_fields = ['cancelled_at', 'refund_processed_at']
