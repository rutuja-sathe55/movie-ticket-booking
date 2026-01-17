"""
Script to create sample data for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_booking_project.settings')
django.setup()

from django.contrib.auth.models import User
from movies.models import Genre, Movie
from theatres.models import Theatre, Screen, Seat, Show
from datetime import datetime, timedelta

# Set admin password
try:
    admin = User.objects.get(username='admin')
    admin.set_password('admin123')
    admin.save()
    print("✓ Admin password updated: admin123")
except:
    print("✗ Could not update admin password")

# Create sample genres
genres_data = [
    {'name': 'Action', 'description': 'Action-packed movies'},
    {'name': 'Drama', 'description': 'Emotional and thought-provoking'},
    {'name': 'Comedy', 'description': 'Funny and entertaining'},
    {'name': 'Thriller', 'description': 'Suspenseful stories'},
    {'name': 'Romance', 'description': 'Romantic stories'},
]

for genre_data in genres_data:
    genre, created = Genre.objects.get_or_create(**genre_data)
    if created:
        print(f"✓ Created genre: {genre.name}")
    else:
        print(f"✓ Genre already exists: {genre.name}")

# Create sample movies
movies_data = [
    {
        'title': 'The Great Adventure',
        'description': 'An epic journey across continents.',
        'release_date': datetime.now().date(),
        'duration_minutes': 150,
        'language': 'english',
        'director': 'John Doe',
        'cast': 'Tom Cruise, Emma Watson',
        'rating': 8.5,
        'certification': 'UA',
        'status': 'running',
        'is_featured': True,
    },
    {
        'title': 'Love in Paris',
        'description': 'A romantic story set in Paris.',
        'release_date': datetime.now().date() + timedelta(days=5),
        'duration_minutes': 120,
        'language': 'hindi',
        'director': 'Jane Smith',
        'cast': 'Deepika Padukone, Ranveer Singh',
        'rating': 7.5,
        'certification': 'UA',
        'status': 'coming_soon',
        'is_featured': False,
    }
]

for movie_data in movies_data:
    movie, created = Movie.objects.get_or_create(
        title=movie_data['title'],
        defaults={k: v for k, v in movie_data.items() if k != 'title'}
    )
    if created:
        # Add genres
        genre = Genre.objects.first()
        if genre:
            movie.genres.add(genre)
        print(f"✓ Created movie: {movie.title}")
    else:
        print(f"✓ Movie already exists: {movie.title}")

# Create sample theatre
theatre, created = Theatre.objects.get_or_create(
    name='CineMax Downtown',
    defaults={
        'address': '123 Cinema Street',
        'city': 'Delhi',
        'state': 'Delhi',
        'postal_code': '110001',
        'phone_number': '+91 9876543210',
        'email': 'info@cinemax.com',
        'total_screens': 5,
        'is_active': True,
        'has_4k': True,
        'has_imax': True,
    }
)
if created:
    print(f"✓ Created theatre: {theatre.name}")
else:
    print(f"✓ Theatre already exists: {theatre.name}")

# Create sample screens
if theatre.screens.count() == 0:
    for i in range(1, 3):
        screen, created = Screen.objects.get_or_create(
            theatre=theatre,
            name=f'Screen {i}',
            defaults={
                'capacity': 100,
                'total_rows': 10,
                'seats_per_row': 10,
                'is_4k': i == 1,
                'is_imax': False,
                'is_dolby': False,
                'is_active': True,
            }
        )
        if created:
            print(f"✓ Created screen: {screen.name}")
            
            # Create seats for this screen
            rows = 'ABCDEFGHIJ'
            for row_idx, row in enumerate(rows[:screen.total_rows]):
                for seat_num in range(1, screen.seats_per_row + 1):
                    Seat.objects.get_or_create(
                        screen=screen,
                        row=row,
                        seat_number=seat_num,
                        defaults={
                            'seat_type': 'premium' if row_idx < 3 else 'standard',
                            'base_price': 200 if row_idx < 3 else 150,
                            'is_available': True,
                            'status': 'available',
                        }
                    )
            print(f"  ✓ Created {screen.total_rows * screen.seats_per_row} seats")

# Create sample shows
movie = Movie.objects.filter(status='running').first()
screen = theatre.screens.first()

if movie and screen:
    show_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    show_date = show_time.date()
    
    for i in range(3):
        show_datetime = show_time + timedelta(hours=3*i)
        show, created = Show.objects.get_or_create(
            screen=screen,
            movie=movie,
            show_date=show_date,
            show_time=show_datetime.time(),
            defaults={
                'end_time': (show_datetime + timedelta(minutes=movie.duration_minutes)).time(),
                'base_ticket_price': 150,
                'status': 'available',
                'is_active': True,
            }
        )
        if created:
            print(f"✓ Created show: {movie.title} at {show_datetime.time()}")

print("\n✓ Sample data setup complete!")
