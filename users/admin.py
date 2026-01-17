"""
Admin configuration for Users app
"""

from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, UserRole, TheatreManager, Staff


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    extra = 0
    fields = ['phone_number', 'address', 'city', 'postal_code', 'date_of_birth', 'is_verified']


class UserRoleInline(admin.TabularInline):
    """Inline admin for UserRole"""
    model = UserRole
    extra = 0


class CustomUserAdmin(admin.ModelAdmin):
    """Extended User admin with profile and role information"""
    inlines = [UserProfileInline, UserRoleInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile"""
    list_display = ['user', 'phone_number', 'city', 'is_verified', 'created_at']
    search_fields = ['user__username', 'phone_number', 'city']
    list_filter = ['is_verified', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin for UserRole"""
    list_display = ['user', 'role']
    search_fields = ['user__username', 'role']
    list_filter = ['role']


@admin.register(TheatreManager)
class TheatreManagerAdmin(admin.ModelAdmin):
    """Admin for TheatreManager"""
    list_display = ['user', 'theatre', 'commission_percentage', 'created_at']
    search_fields = ['user__username', 'theatre__name']
    list_filter = ['created_at']
    readonly_fields = ['created_at']


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    """Admin for Staff"""
    list_display = ['user', 'theatre', 'department', 'is_active', 'hired_date']
    search_fields = ['user__username', 'theatre__name']
    list_filter = ['department', 'is_active', 'hired_date']


# Unregister and re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
