"""
URL configuration for Utils app
"""

from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    # API endpoints
    path('api/seats/<int:show_id>/', views.get_available_seats_api, name='available_seats_api'),
    path('api/seat-status/<int:show_id>/', views.get_seat_status_api, name='seat_status_api'),
]
