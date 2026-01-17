"""
Forms for Theatres app
"""

from django import forms
from .models import Theatre, Screen, Show, Seat
from datetime import datetime, timedelta


class TheatreSelectionForm(forms.Form):
    """
    Form to select a theatre for booking
    """
    city = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Select or Enter City'
        }),
        required=True
    )


class ShowSelectionForm(forms.Form):
    """
    Form to select a show (movie, theatre, date, time)
    """
    movie = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label='Select Movie'
    )
    theatre = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label='Select Theatre'
    )
    show_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': datetime.now().date().isoformat()
        }),
        required=True,
        label='Select Date'
    )
    show = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label='Select Time'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Will be populated dynamically based on selected movie/theatre/date
        self.fields['show'].queryset = Show.objects.none()


class SeatSelectionForm(forms.Form):
    """
    Form for seat selection during booking
    """
    seats = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label='Select Seats'
    )
    
    def __init__(self, show=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if show:
            from bookings.models import Ticket
            # Get booked seats for this show
            booked_seat_ids = Ticket.objects.filter(show=show).values_list('seat_id', flat=True)
            # Show only available seats
            self.fields['seats'].queryset = show.screen.seats.filter(
                is_available=True
            ).exclude(id__in=booked_seat_ids)
        else:
            self.fields['seats'].queryset = Seat.objects.none()
