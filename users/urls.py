"""
URL configuration for Users app
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    
    # User Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    
    # Email verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
]
