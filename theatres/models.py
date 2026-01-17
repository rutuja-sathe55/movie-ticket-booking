"""
Theatres App Models
- Theatre information
- Screens/Halls within a theatre
- Shows (movie screenings) with timings
- Seats and their availability
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class Theatre(models.Model):
    """
    Cinema theatre/multiplex information
    """
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    
    # Theatre details
    total_screens = models.IntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    
    # Map location (for future Google Maps integration)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Theatre amenities
    has_4k = models.BooleanField(default=False)
    has_imax = models.BooleanField(default=False)
    has_dolby = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Theatre"
        verbose_name_plural = "Theatres"
        ordering = ['city', 'name']
        indexes = [
            models.Index(fields=['city', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    def get_absolute_url(self):
        """Return the URL to access this theatre's page"""
        return reverse('theatres:theatre_detail', kwargs={'pk': self.pk})


class Screen(models.Model):
    """
    Individual screens/halls within a theatre
    Each screen has its own seats and shows
    """
    theatre = models.ForeignKey(Theatre, on_delete=models.CASCADE, related_name='screens')
    name = models.CharField(max_length=100, help_text="e.g., Screen 1, Screen 2, IMAX Hall")
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Screen details
    total_rows = models.IntegerField(validators=[MinValueValidator(1)])
    seats_per_row = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Screen technology
    is_4k = models.BooleanField(default=False)
    is_imax = models.BooleanField(default=False)
    is_dolby = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Screen"
        verbose_name_plural = "Screens"
        unique_together = ['theatre', 'name']
    
    def __str__(self):
        return f"{self.theatre.name} - {self.name}"
    
    def get_available_seats(self):
        """Get count of available seats"""
        return self.seats.filter(is_available=True).count()


class Seat(models.Model):
    """
    Individual seats in a screen
    """
    SEAT_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
        ('couple', 'Couple Seat'),
    ]
    
    SEAT_STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('blocked', 'Blocked'),
    ]
    
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=2)  # A, B, C, etc.
    seat_number = models.IntegerField()  # 1, 2, 3, etc.
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE_CHOICES, default='standard')
    is_available = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=SEAT_STATUS_CHOICES, default='available')
    
    # Pricing
    base_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Seat"
        verbose_name_plural = "Seats"
        unique_together = ['screen', 'row', 'seat_number']
        ordering = ['row', 'seat_number']
    
    def __str__(self):
        return f"{self.screen.theatre.name} - {self.screen.name} - {self.row}{self.seat_number}"


class Show(models.Model):
    """
    Movie show/screening at a specific theatre, screen, and time
    Links Movie to Theatre with timing information
    """
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='shows')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='shows')
    
    # Show timing
    show_date = models.DateField()
    show_time = models.TimeField()
    end_time = models.TimeField()  # Calculated based on movie duration
    
    # Pricing
    base_ticket_price = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Base price for standard seats"
    )
    
    # Status
    SHOW_STATUS_CHOICES = [
        ('available', 'Available for Booking'),
        ('housefull', 'House Full'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=SHOW_STATUS_CHOICES, default='available')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Show"
        verbose_name_plural = "Shows"
        ordering = ['show_date', 'show_time']
        indexes = [
            models.Index(fields=['show_date', 'screen']),
            models.Index(fields=['movie', 'show_date']),
        ]
    
    def __str__(self):
        return f"{self.movie.title} at {self.screen.theatre.name} - {self.show_date} {self.show_time}"
    
    def get_available_seats_count(self):
        """Get count of available seats for this show"""
        from bookings.models import Ticket
        booked_seats = Ticket.objects.filter(show=self).values_list('seat_id', flat=True)
        return self.screen.seats.filter(is_available=True).exclude(id__in=booked_seats).count()
