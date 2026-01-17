"""
Movies App Models
- Movie information and details
- Genre classification
- Movie search and filtering
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class Genre(models.Model):
    """
    Movie genres (Action, Drama, Comedy, etc.)
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
    
    def __str__(self):
        return self.name


class Movie(models.Model):
    """
    Main Movie model with detailed information
    """
    STATUS_CHOICES = [
        ('coming_soon', 'Coming Soon'),
        ('running', 'Running'),
        ('ended', 'Ended'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    poster = models.ImageField(upload_to='movie_posters/')
    banner = models.ImageField(upload_to='movie_banners/', blank=True, null=True)
    release_date = models.DateField()
    duration_minutes = models.IntegerField(validators=[MinValueValidator(1)])  # Duration in minutes
    language = models.CharField(max_length=50, choices=[
        ('hindi', 'Hindi'),
        ('english', 'English'),
        ('marathi', 'Marathi'),
        
    ])
    genres = models.ManyToManyField(Genre, related_name='movies')
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        default=0.0,
        help_text="IMDb rating out of 10"
    )
    director = models.CharField(max_length=255, blank=True, null=True)
    cast = models.TextField(blank=True, null=True, help_text="Comma-separated actor names")
    certification = models.CharField(max_length=10, choices=[
        ('U', 'U - Unrestricted'),
        ('UA', 'UA - Restricted for Children'),
        ('A', 'A - Restricted to Adults'),
        ('S', 'S - Restricted to Specialized'),
    ], default='UA')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='coming_soon')
    is_featured = models.BooleanField(default=False, help_text="Display on homepage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Movie"
        verbose_name_plural = "Movies"
        ordering = ['-release_date']
        indexes = [
            models.Index(fields=['status', '-release_date']),
            models.Index(fields=['title']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Return the URL to access this movie detail page"""
        return reverse('movies:movie_detail', kwargs={'pk': self.pk})
    
    def get_duration_display(self):
        """Convert minutes to hours and minutes format"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}h {minutes}m"
    
    def get_genres_display(self):
        """Return comma-separated genres"""
        return ', '.join([g.name for g in self.genres.all()])


class MovieReview(models.Model):
    """
    User reviews and ratings for movies
    """
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='movie_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)  # User has booked tickets for this movie
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Movie Review"
        verbose_name_plural = "Movie Reviews"
        unique_together = ['movie', 'user']  # One review per user per movie
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.movie.title} - {self.user.username} ({self.rating}★)"
