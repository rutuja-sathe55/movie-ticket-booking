"""
Forms for Payments app
"""

from django import forms
from .models import Payment, PaymentMethod


class PaymentForm(forms.ModelForm):
    """
    Form for processing payments
    """
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Payment Method',
        required=True
    )
    
    class Meta:
        model = Payment
        fields = ['payment_method']


class RazorpayPaymentForm(forms.Form):
    """
    Form for Razorpay payment processing
    """
    razorpay_order_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    razorpay_payment_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    razorpay_signature = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
