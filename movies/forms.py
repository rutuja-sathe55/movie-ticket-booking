"""
Forms for Movies app
"""

from django import forms
from .models import MovieReview, Movie


class MovieForm(forms.ModelForm):
    """
    Form for creating/updating Movie instances
    """
    class Meta:
        model = Movie
        fields = [
            'title', 'description', 'poster', 'banner', 'release_date',
            'duration_minutes', 'language', 'genres', 'rating', 'director',
            'cast', 'certification', 'status', 'is_featured'
        ]
        widgets = {
            'release_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'genres': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 0, 'max': 10}),
            'director': forms.TextInput(attrs={'class': 'form-control'}),
            'cast': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'certification': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MovieReviewForm(forms.ModelForm):
    """
    Form for users to submit movie reviews
    """
    RATING_CHOICES = [
        (1, '1 Star - Poor'),
        (2, '2 Stars - Fair'),
        (3, '3 Stars - Good'),
        (4, '4 Stars - Very Good'),
        (5, '5 Stars - Excellent'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'rating-radio'}),
        label='Your Rating',
        required=True,
        error_messages={
            'required': 'Please select a rating.',
        }
    )
    
    class Meta:
        model = MovieReview
        fields = ['rating', 'review_text']
        widgets = {
            'review_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your thoughts about this movie...'
            })
        }


class MovieSearchForm(forms.Form):
    """
    Form for searching and filtering movies
    """
    LANGUAGE_CHOICES = [
        ('', 'All Languages'),
        ('hindi', 'Hindi'),
        ('english', 'English'),
        ('tamil', 'Tamil'),
        ('telugu', 'Telugu'),
        ('kannada', 'Kannada'),
        ('malayalam', 'Malayalam'),
    ]
    
    CERTIFICATION_CHOICES = [
        ('', 'All Certificates'),
        ('U', 'U - Unrestricted'),
        ('UA', 'UA - Restricted for Children'),
        ('A', 'A - Restricted to Adults'),
        ('S', 'S - Restricted to Specialized'),
    ]
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search movies...'
        })
    )
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    certification = forms.ChoiceField(
        choices=CERTIFICATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    genre = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by genre'
        })
    )
