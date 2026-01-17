"""
Admin configuration for Food app
"""

from django.contrib import admin
from .models import FoodCategory, FoodItem, FoodOrder, FoodOrderItem, FoodReview


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    """Admin for FoodCategory"""
    list_display = ['name']
    search_fields = ['name']


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    """Admin for FoodItem"""
    list_display = ['name', 'category', 'price', 'available_quantity', 'is_available', 'is_vegetarian']
    search_fields = ['name', 'category__name']
    list_filter = ['category', 'is_available', 'is_vegetarian', 'contains_nuts', 'contains_dairy']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'image')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'quantity_unit', 'available_quantity', 'is_available')
        }),
        ('Properties', {
            'fields': ('is_vegetarian', 'contains_nuts', 'contains_dairy', 'contains_gluten')
        }),
    )


class FoodOrderItemInline(admin.TabularInline):
    """Inline admin for FoodOrderItem"""
    model = FoodOrderItem
    extra = 0
    readonly_fields = ['created_at']


@admin.register(FoodOrder)
class FoodOrderAdmin(admin.ModelAdmin):
    """Admin for FoodOrder"""
    list_display = ['order_id', 'user', 'theatre', 'final_amount', 'status', 'created_at']
    search_fields = ['order_id', 'user__username']
    list_filter = ['status', 'theatre', 'created_at']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    inlines = [FoodOrderItemInline]
    date_hierarchy = 'created_at'


@admin.register(FoodOrderItem)
class FoodOrderItemAdmin(admin.ModelAdmin):
    """Admin for FoodOrderItem"""
    list_display = ['food_order', 'food_item', 'quantity', 'total_price']
    search_fields = ['food_order__order_id', 'food_item__name']
    list_filter = ['created_at']


@admin.register(FoodReview)
class FoodReviewAdmin(admin.ModelAdmin):
    """Admin for FoodReview"""
    list_display = ['food_item', 'user', 'rating', 'created_at']
    search_fields = ['food_item__name', 'user__username']
    list_filter = ['rating', 'created_at']
