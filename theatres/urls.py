"""
URL configuration for Theatres app
"""

from django.urls import path
from . import views

app_name = 'theatres'

urlpatterns = [
    # Theatre listing and details
    path('', views.theatre_list, name='theatre_list'),
    path('<int:pk>/', views.theatre_detail, name='theatre_detail'),
    
    # Show and seat selection
    path('shows/available/', views.get_available_shows, name='get_available_shows'),
    path('show/<int:show_id>/seats/', views.seat_layout, name='seat_layout'),
    path('show/<int:show_id>/seat-status/', views.get_seat_status, name='get_seat_status'),
    
    # Theatre management
    path('<int:theatre_id>/manage-screens/', views.screen_management, name='screen_management'),
]
