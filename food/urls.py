"""
URL configuration for Food app
"""

from django.urls import path
from . import views

app_name = 'food'

urlpatterns = [
    # Menu and items
    path('menu/', views.menu, name='menu'),
    path('menu/<int:theatre_id>/', views.menu, name='menu_by_theatre'),
    path('<int:pk>/', views.food_detail, name='food_detail'),
    path('<int:food_id>/review/', views.submit_food_review, name='submit_review'),
    
    # Shopping cart
    path('cart/add/<int:food_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/view/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:food_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Food orders
    path('order/create/', views.create_food_order, name='create_order'),
    path('order/<int:booking_id>/create/', views.create_food_order, name='create_order_for_booking'),
    path('order/<int:pk>/', views.food_order_detail, name='order_detail'),
    path('order/<int:pk>/cancel/', views.cancel_food_order, name='cancel_order'),
    path('orders/', views.food_order_list, name='order_list'),
]
