"""
URL configuration for Bookings app
"""

from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Booking creation and management
    path('create/', views.create_booking, name='create_booking'),
    path('<int:pk>/', views.booking_detail, name='booking_detail'),
    path('', views.booking_list, name='booking_list'),
    path('<int:pk>/confirm/', views.booking_confirmation, name='booking_confirmation'),
    # Download all tickets for a booking as a single PDF
    path('<int:pk>/download/', views.booking_download, name='booking_download'),
    
    # Ticket operations
    path('ticket/<str:ticket_id>/preview/', views.ticket_preview, name='ticket_preview'),
    path('ticket/<str:ticket_id>/download/', views.download_ticket, name='download_ticket'),
    
    # Cancellation
    path('<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
]
