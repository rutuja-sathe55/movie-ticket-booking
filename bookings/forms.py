"""
Forms for Bookings app
"""

from django import forms
from .models import Booking, Ticket, BookingCancellation


class BookingForm(forms.ModelForm):
    """
    Form for creating a new booking
    """
    class Meta:
        model = Booking
        fields = ['discount_amount']
        widgets = {
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter discount amount (if any)',
                'min': '0',
                'step': '0.01'
            })
        }


class TicketForm(forms.ModelForm):
    """
    Form for individual ticket details
    """
    class Meta:
        model = Ticket
        fields = ['base_price', 'tax']
        widgets = {
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
        }


class BookingCancellationForm(forms.ModelForm):
    """
    Form for cancelling a booking
    """
    class Meta:
        model = BookingCancellation
        fields = ['cancellation_reason', 'cancellation_charges']
        widgets = {
            'cancellation_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter reason for cancellation'
            }),
            'cancellation_charges': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Cancellation charges'
            })
        }
