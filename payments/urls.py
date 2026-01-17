"""
URL configuration for Payments app
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # List payment methods available to users
    path('methods/', views.payment_methods, name='payment_methods'),
    # Initiate payment for non-booking orders (e.g. food)
    path('initiate/<str:order_type>/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    # Use a payment method for a pending booking (booking id optional via ?booking=)
    path('methods/use/<int:method_id>/', views.use_payment_method, name='use_payment_method'),
    # Payment processing
    path('booking/<int:booking_id>/', views.payment_gateway, name='payment_gateway'),
    path('<int:payment_id>/checkout/', views.razorpay_checkout, name='razorpay_checkout'),
    path('callback/', views.razorpay_callback, name='razorpay_callback'),
    
    # Payment status
    path('<int:payment_id>/success/', views.payment_success, name='payment_success'),
    path('<int:payment_id>/failed/', views.payment_failed, name='payment_failed'),
    path('<int:payment_id>/retry/', views.retry_payment, name='retry_payment'),
    path('<int:payment_id>/simulate/', views.simulate_payment, name='simulate_payment'),
    
    # Invoice
    path('<int:payment_id>/invoice/', views.invoice_view, name='invoice'),
]
