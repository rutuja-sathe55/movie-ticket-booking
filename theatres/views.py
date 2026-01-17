"""
Views for Theatres app
- Display theatres list
- Theatre details with available shows
- Seat layout and selection
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import Theatre, Screen, Show, Seat
from .forms import TheatreSelectionForm, ShowSelectionForm, SeatSelectionForm
from movies.models import Movie
from datetime import datetime, timedelta


def theatre_list(request):
    """
    Display list of all theatres with city filter
    """
    city = request.GET.get('city')
    theatres = Theatre.objects.filter(is_active=True)
    
    if city:
        theatres = theatres.filter(city__icontains=city)
    
    # Get unique cities
    cities = Theatre.objects.filter(is_active=True).values_list('city', flat=True).distinct()
    
    context = {
        'theatres': theatres,
        'cities': cities,
        'selected_city': city,
        'page_title': 'Select Theatre',
    }
    return render(request, 'theatres/theatre_list.html', context)


def theatre_detail(request, pk):
    """
    Display detailed information about a theatre with available shows
    """
    theatre = get_object_or_404(Theatre, pk=pk, is_active=True)
    selected_date = request.GET.get('date', datetime.now().date().isoformat())
    
    try:
        show_date = datetime.fromisoformat(selected_date).date()
    except:
        show_date = datetime.now().date()
    
    # Get shows for this theatre on selected date
    shows = Show.objects.filter(
        screen__theatre=theatre,
        show_date=show_date,
        is_active=True
    ).select_related('movie', 'screen').order_by('show_time')

    # Build screens info with shows and seat counts to display full details in template
    screens_qs = theatre.screens.filter(is_active=True).prefetch_related('seats')
    screens_info = []
    for screen in screens_qs:
        screen_shows = []
        for sh in shows.filter(screen=screen):
            mv = sh.movie
            poster_url = None
            try:
                if mv.poster and hasattr(mv.poster, 'url'):
                    poster_url = mv.poster.url
            except Exception:
                poster_url = None

            screen_shows.append({
                'id': sh.id,
                'movie_id': mv.id,
                'movie_title': mv.title,
                'poster_url': poster_url,
                'show_time': sh.show_time,
                'end_time': sh.end_time,
                'base_ticket_price': sh.base_ticket_price,
                'status': sh.status,
                'available_seats': sh.get_available_seats_count(),
                'duration': mv.get_duration_display() if hasattr(mv, 'get_duration_display') else None,
                'genres': mv.get_genres_display() if hasattr(mv, 'get_genres_display') else None,
                'rating': getattr(mv, 'rating', None),
                'director': getattr(mv, 'director', None),
                'cast': getattr(mv, 'cast', None),
                'certification': getattr(mv, 'certification', None),
                'description': getattr(mv, 'description', '')[:300],
            })

        screens_info.append({
            'screen': screen,
            'capacity': screen.seats.count(),
            'total_rows': getattr(screen, 'total_rows', None),
            'seats_per_row': getattr(screen, 'seats_per_row', None),
            'shows': screen_shows,
        })

    # Total seats across all screens
    total_seats = sum(i['capacity'] for i in screens_info)

    # Build a simple description/facilities string if model doesn't have description
    facilities = []
    if theatre.has_4k:
        facilities.append('4K')
    if theatre.has_imax:
        facilities.append('IMAX')
    if theatre.has_dolby:
        facilities.append('Dolby')
    description = theatre.__dict__.get('description') or (', '.join(facilities) if facilities else '')
    
    # Get available dates (next 7 days)
    available_dates = [datetime.now().date() + timedelta(days=i) for i in range(7)]
    
    context = {
        'theatre': theatre,
        'shows': shows,
        'screens_info': screens_info,
        'total_seats': total_seats,
        'description': description,
        'selected_date': show_date,
        'available_dates': available_dates,
        'page_title': theatre.name,
    }
    return render(request, 'theatres/theatre_detail.html', context)


@require_http_methods(["GET"])
def get_available_shows(request):
    """
    AJAX endpoint to get available shows for a selected movie, theatre, and date
    """
    movie_id = request.GET.get('movie_id')
    theatre_id = request.GET.get('theatre_id')
    show_date = request.GET.get('date')
    
    shows = Show.objects.filter(
        movie_id=movie_id,
        screen__theatre_id=theatre_id,
        show_date=show_date,
        is_active=True,
        status='available'
    ).values('id', 'show_time', 'end_time', 'base_ticket_price')
    
    return JsonResponse({
        'shows': list(shows)
    })


def seat_layout(request, show_id):
    """
    Display seat layout for a selected show
    """
    show = get_object_or_404(Show, id=show_id, is_active=True)
    seats_qs = show.screen.seats.all().order_by('row', 'seat_number')

    # If no seats exist for this screen, auto-generate seats based on screen configuration
    seats = list(seats_qs)
    if not seats:
        screen = show.screen
        # Determine rows as letters A, B, C... based on total_rows
        total_rows = getattr(screen, 'total_rows', None) or 0
        seats_per_row = getattr(screen, 'seats_per_row', None) or 0
        # Safety checks
        try:
            total_rows = int(total_rows)
            seats_per_row = int(seats_per_row)
        except Exception:
            total_rows = 0
            seats_per_row = 0

        rows = []
        for i in range(total_rows):
            # Support beyond 26 rows by repeating letters (AA, AB...)
            letter = ''
            n = i
            while True:
                letter = chr(ord('A') + (n % 26)) + letter
                n = n // 26 - 1
                if n < 0:
                    break
            rows.append(letter)

        created_seats = []
        for r in rows:
            for sn in range(1, seats_per_row + 1):
                s = Seat.objects.create(
                    screen=screen,
                    row=r,
                    seat_number=sn,
                    seat_type='standard',
                    is_available=True,
                    status='available',
                    base_price=show.base_ticket_price or 0
                )
                created_seats.append(s)

        seats = created_seats
    
    # Group seats by row
    seats_by_row = {}
    for seat in seats:
        # seat may be dict-like if using values(), ensure attribute access
        row_key = getattr(seat, 'row', None) or (seat.get('row') if isinstance(seat, dict) else None)
        if row_key not in seats_by_row:
            seats_by_row[row_key] = []
        seats_by_row[row_key].append(seat)
    
    # Get booked seats
    from bookings.models import Ticket
    booked_seat_ids = Ticket.objects.filter(show=show).values_list('seat_id', flat=True)
    
    context = {
        'show': show,
        'seats_by_row': seats_by_row,
        'booked_seat_ids': booked_seat_ids,
        'page_title': f'Select Seats - {show.movie.title}',
    }
    return render(request, 'theatres/seat_layout.html', context)


@require_http_methods(["GET"])
def get_seat_status(request, show_id):
    """
    AJAX endpoint to get seat availability status for a show
    """
    show = get_object_or_404(Show, id=show_id)
    seats = show.screen.seats.all().values('id', 'row', 'seat_number', 'seat_type', 'base_price')
    
    # Get booked seats
    from bookings.models import Ticket
    booked_seat_ids = list(Ticket.objects.filter(show=show).values_list('seat_id', flat=True))
    
    seats_data = []
    for seat in seats:
        seats_data.append({
            'id': seat['id'],
            'row': seat['row'],
            'seat_number': seat['seat_number'],
            'type': seat['seat_type'],
            'price': float(seat['base_price']),
            'is_booked': seat['id'] in booked_seat_ids
        })
    
    return JsonResponse({
        'seats': seats_data,
        'available_count': show.get_available_seats_count()
    })


def screen_management(request, theatre_id):
    """
    View for theatre managers to manage screens and seats (admin view)
    """
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    try:
        theatre_manager = request.user.theatre_manager_profile
        if theatre_manager.theatre_id != theatre_id:
            return redirect('home')
    except:
        return redirect('home')
    
    theatre = get_object_or_404(Theatre, pk=theatre_id)
    screens = theatre.screens.all()
    
    context = {
        'theatre': theatre,
        'screens': screens,
        'page_title': f'Manage Screens - {theatre.name}',
    }
    return render(request, 'theatres/screen_management.html', context)
