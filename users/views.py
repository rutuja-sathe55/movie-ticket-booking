"""
Views for Users app
- User registration, login, logout
- Profile viewing and editing
- User authentication
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import UserProfile, UserRole
from bookings.models import Booking


@require_http_methods(["GET", "POST"])
def register(request):
    """
    User registration view
    Handles both GET (display form) and POST (process registration)
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('movies:movie_list')
        else:
            messages.error(request, 'Error in registration. Please check the form.')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'page_title': 'Register'
    }
    return render(request, 'users/register.html', context)


@require_http_methods(["GET", "POST"])
def login_user(request):
    """
    User login view
    Handles both GET (display form) and POST (process login)
    """
    if request.user.is_authenticated:
        return redirect('movies:movie_list')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('movies:movie_list')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
        'page_title': 'Login'
    }
    return render(request, 'users/login.html', context)


@login_required(login_url='users:login')
def logout_user(request):
    """
    User logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required(login_url='users:login')
def profile(request):
    """
    View user profile with all information
    """
    # Get or create UserProfile and UserRole if they don't exist
    user_profile, created_profile = UserProfile.objects.get_or_create(user=request.user)
    user_role, created_role = UserRole.objects.get_or_create(user=request.user, defaults={'role': 'customer'})
    
    # find latest pending booking for quick-pay from profile (if any)
    pending_booking = Booking.objects.filter(user=request.user, status='pending').order_by('-created_at').first()

    context = {
        'profile': user_profile,
        'user_role': user_role,
        'pending_booking': pending_booking,
        'page_title': 'My Profile'
    }
    return render(request, 'users/profile.html', context)


@login_required(login_url='users:login')
@require_http_methods(["GET", "POST"])
def edit_profile(request):
    """
    Edit user profile view
    """
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            # Update user information
            request.user.first_name = form.cleaned_data.get('first_name')
            request.user.last_name = form.cleaned_data.get('last_name')
            request.user.email = form.cleaned_data.get('email')
            request.user.save()
            
            # Save profile
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Error updating profile. Please check the form.')
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'form': form,
        'page_title': 'Edit Profile'
    }
    return render(request, 'users/edit_profile.html', context)


@login_required(login_url='users:login')
def user_dashboard(request):
    """
    User dashboard showing bookings, orders, etc.
    Different content based on user role
    """
    user_role, created = UserRole.objects.get_or_create(user=request.user, defaults={'role': 'customer'})
    
    context = {
        'user_role': user_role,
        'page_title': 'Dashboard'
    }
    
    if user_role.role == 'customer':
        # Load customer-specific data
        from bookings.models import Booking
        recent_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')[:5]
        context['recent_bookings'] = recent_bookings
        return render(request, 'users/customer_dashboard.html', context)
    
    elif user_role.role == 'theatre_manager':
        # Load theatre manager-specific data
        from theatres.models import Theatre
        from bookings.models import Booking
        
        try:
            theatre_manager = request.user.theatre_manager_profile
            theatre = theatre_manager.theatre
            context['theatre'] = theatre
            context['total_bookings'] = Booking.objects.filter(show__theatre=theatre).count()
            return render(request, 'users/manager_dashboard.html', context)
        except:
            messages.warning(request, 'No theatre assigned to your account.')
            return render(request, 'users/user_dashboard.html', context)
    
    elif user_role.role == 'staff':
        # Load staff-specific data
        from food.models import FoodOrder
        
        try:
            staff = request.user.staff_profile
            pending_orders = FoodOrder.objects.filter(
                theatre=staff.theatre,
                status='pending'
            ).order_by('-created_at')
            context['pending_orders'] = pending_orders
            return render(request, 'users/staff_dashboard.html', context)
        except:
            messages.warning(request, 'No theatre assigned to your staff account.')
            return render(request, 'users/user_dashboard.html', context)
    
    else:
        return render(request, 'users/user_dashboard.html', context)


def verify_email(request, token):
    """
    Verify user email with token (for future email verification feature)
    """
    messages.info(request, 'Email verification will be implemented soon.')
    return redirect('users:profile')
