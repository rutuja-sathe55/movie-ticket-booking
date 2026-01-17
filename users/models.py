"""
Users App Models
- User profile with role-based access (Admin, Theatre Manager, Customer, Staff)
- User authentication and registration
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserRole(models.Model):
    """
    Define different roles for users in the system.
    Roles: Admin, Theatre Manager, Customer, Staff, Guest
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('theatre_manager', 'Theatre Manager'),
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('guest', 'Guest'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
    
    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class UserProfile(models.Model):
    """
    Extended user profile with additional information.
    Connected to Django's built-in User model via OneToOneField.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"Profile of {self.user.username}"


class TheatreManager(models.Model):
    """
    Extended profile for Theatre Manager role.
    Links a user to the theatre they manage.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='theatre_manager_profile')
    theatre = models.ForeignKey('theatres.Theatre', on_delete=models.SET_NULL, null=True, blank=True, related_name='managers')
    commission_percentage = models.FloatField(default=5.0)  # Commission earned per booking
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Theatre Manager"
        verbose_name_plural = "Theatre Managers"
    
    def __str__(self):
        return f"{self.user.username} - Manager"


class Staff(models.Model):
    """
    Staff profile for food preparation and order management.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    theatre = models.ForeignKey('theatres.Theatre', on_delete=models.CASCADE, related_name='staff_members')
    department = models.CharField(max_length=50, choices=[
        ('food', 'Food Preparation'),
        ('counter', 'Counter'),
        ('delivery', 'Delivery'),
    ], default='food')
    is_active = models.BooleanField(default=True)
    hired_date = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Staff"
        verbose_name_plural = "Staff"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_department_display()}"


# Signal handlers for automatic profile creation
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create UserProfile when a new User is created
    """
    if created:
        UserProfile.objects.create(user=instance)
        UserRole.objects.create(user=instance, role='guest')


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to automatically save UserProfile when User is saved
    """
    instance.profile.save()
