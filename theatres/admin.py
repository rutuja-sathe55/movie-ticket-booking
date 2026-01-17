"""
Admin configuration for Theatres app
"""

from django.contrib import admin
from theatres.models import Theatre, Screen, Seat, Show
# from .models import Theatre, Screen, Seat, Show


# @admin.register(Theatre)
# class TheatreAdmin(admin.ModelAdmin):
#     """Admin for Theatre"""
#     list_display = ['name', 'city', 'total_screens', 'is_active', 'phone_number']
#     search_fields = ['name', 'city', 'address']
#     list_filter = ['city', 'is_active', 'has_4k', 'has_imax', 'has_dolby']
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('name', 'address', 'city', 'state', 'postal_code')
#         }),
#         ('Contact', {
#             'fields': ('phone_number', 'email')
#         }),
#         ('Theatre Details', {
#             'fields': ('total_screens', 'is_active')
#         }),
#         ('Amenities', {
#             'fields': ('has_4k', 'has_imax', 'has_dolby')
#         }),
#         ('Location', {
#             'fields': ('latitude', 'longitude'),
#             'classes': ('collapse',)
#         }),
#     )


# @admin.register(Screen)
# class ScreenAdmin(admin.ModelAdmin):
#     """Admin for Screen"""
#     list_display = ['name', 'theatre', 'capacity', 'total_rows', 'seats_per_row', 'is_active']
#     search_fields = ['name', 'theatre__name']
#     list_filter = ['theatre', 'is_active', 'is_4k', 'is_imax', 'is_dolby']
#     readonly_fields = ['created_at']


# @admin.register(Seat)
# class SeatAdmin(admin.ModelAdmin):
#     """Admin for Seat"""
#     list_display = ['seat_display', 'seat_type', 'status', 'base_price', 'is_available']
#     search_fields = ['screen__name', 'screen__theatre__name']
#     list_filter = ['screen', 'seat_type', 'status', 'is_available']  # fixed: removed related lookup
#     readonly_fields = ['created_at']

#     def seat_display(self, obj):
#         return str(obj)
#     seat_display.short_description = 'Seat'
#     seat_display.admin_order_field = 'id'


# @admin.register(Show)
# class ShowAdmin(admin.ModelAdmin):
#     """Admin for Show"""
#     list_display = ['movie', 'screen', 'show_date', 'show_time', 'base_ticket_price', 'status']
#     search_fields = ['movie__title', 'screen__name', 'screen__theatre__name']
#     list_filter = ['show_date', 'status', 'screen', 'movie']  # fixed: removed related lookup
#     readonly_fields = ['created_at', 'updated_at']
#     date_hierarchy = 'show_date'

from theatres.models import Theatre, Screen, Seat, Show

# DO NOT perform database writes at import time. The previous version of this
# module created sample Theatre/Screen/Show rows during module import which
# causes database access while Django is initializing apps and leads to
# runtime warnings/errors. Move any seeding logic into a management command
# or a data migration. For now, only register models with the admin.

from django.contrib import admin


admin.site.register(Theatre)
admin.site.register(Screen)
admin.site.register(Seat)
admin.site.register(Show)
