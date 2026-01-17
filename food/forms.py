"""
Forms for Food app
"""

from django import forms
from .models import FoodOrder, FoodOrderItem, FoodItem, FoodReview


class FoodItemForm(forms.ModelForm):
    """
    Form for managing food items (Admin view)
    """
    class Meta:
        model = FoodItem
        fields = ['name', 'description', 'category', 'price', 'quantity_unit', 'available_quantity', 'image', 'is_available', 'is_vegetarian']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity_unit': forms.TextInput(attrs={'class': 'form-control'}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class FoodOrderForm(forms.ModelForm):
    """
    Form for creating a food order
    """
    class Meta:
        model = FoodOrder
        fields = ['special_instructions']
        widgets = {
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any special requests here'
            })
        }


class FoodOrderItemForm(forms.ModelForm):
    """
    Form for adding items to food order
    """
    food_item = forms.ModelChoiceField(
        queryset=FoodItem.objects.filter(is_available=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Item'
    )
    
    class Meta:
        model = FoodOrderItem
        fields = ['food_item', 'quantity', 'special_instructions']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any special requests for this item?'
            })
        }


class FoodReviewForm(forms.ModelForm):
    """
    Form for submitting food reviews
    """
    rating = forms.IntegerField(
        widget=forms.RadioSelect(choices=[(i, f'{i} Stars') for i in range(1, 6)]),
        label='Your Rating'
    )
    
    class Meta:
        model = FoodReview
        fields = ['rating', 'review_text']
        widgets = {
            'review_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your experience with this food item...'
            })
        }
