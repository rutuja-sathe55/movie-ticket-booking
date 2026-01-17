"""
Food App Models
- FoodItem: Menu items (Popcorn, Drinks, Snacks, etc.)
- FoodOrder: Customer food orders
- FoodOrderItem: Individual items in an order
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse


class FoodCategory(models.Model):
    """
    Categories for food items (Popcorn, Drinks, Snacks, Combos, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='food_icons/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Food Category"
        verbose_name_plural = "Food Categories"
    
    def __str__(self):
        return self.name


class FoodItem(models.Model):
    """
    Individual food items available for ordering
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(FoodCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    
    # Pricing and quantity
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_unit = models.CharField(max_length=50, default='piece')  # piece, litre, kg, etc.
    available_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    
    # Image
    image = models.ImageField(upload_to='food_items/')
    
    # Status
    is_available = models.BooleanField(default=True)
    is_vegetarian = models.BooleanField(default=False)
    
    # Allergens
    contains_nuts = models.BooleanField(default=False)
    contains_dairy = models.BooleanField(default=False)
    contains_gluten = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Item"
        verbose_name_plural = "Food Items"
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('food:food_detail', kwargs={'pk': self.pk})


class FoodOrder(models.Model):
    """
    Food order placed by a customer during booking
    """
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='food_orders')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='food_orders')
    theatre = models.ForeignKey('theatres.Theatre', on_delete=models.CASCADE, related_name='food_orders')
    
    # Order details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    special_instructions = models.TextField(blank=True, null=True)
    
    # Staff assigned
    assigned_staff = models.ForeignKey('users.Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_ready_time = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Food Order"
        verbose_name_plural = "Food Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['order_id']),
        ]
    
    def __str__(self):
        return f"Food Order #{self.order_id}"
    
    def save(self, *args, **kwargs):
        """Generate unique order ID"""
        if not self.order_id:
            import uuid
            self.order_id = f"FO{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class FoodOrderItem(models.Model):
    """
    Individual food items in a food order (line items)
    """
    food_order = models.ForeignKey(FoodOrder, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='order_items')
    
    # Order details
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Special requests
    special_instructions = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Food Order Item"
        verbose_name_plural = "Food Order Items"
    
    def __str__(self):
        return f"{self.quantity}x {self.food_item.name} - Order #{self.food_order.order_id}"


class FoodReview(models.Model):
    """
    Reviews for food items
    """
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='food_reviews')
    rating = models.IntegerField(choices=[(i, f'{i} Stars') for i in range(1, 6)])
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Review"
        verbose_name_plural = "Food Reviews"
        unique_together = ['food_item', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.food_item.name} ({self.rating}★)"
