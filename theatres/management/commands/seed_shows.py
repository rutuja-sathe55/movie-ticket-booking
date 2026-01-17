from django.core.management.base import BaseCommand
from django.db import transaction
from theatres.models import Theatre, Screen, Seat, Show
from movies.models import Movie
from datetime import datetime, time, timedelta


DEFAULT_TIMES = [time(10, 0), time(13, 30), time(17, 0), time(20, 30)]


class Command(BaseCommand):
    help = 'Ensure seats exist for every screen and create shows for next N days for all screens'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Number of days to create shows for (starting today)')
        parser.add_argument('--times', type=str, default=None, help='Comma-separated times (HH:MM) to create shows each day')
        parser.add_argument('--price', type=int, default=200, help='Base ticket price for shows')
        parser.add_argument('--rows', type=int, default=10, help='Number of seat rows to ensure')
        parser.add_argument('--cols', type=int, default=10, help='Number of seats per row to ensure')

    def handle(self, *args, **options):
        days = options['days']
        times_arg = options['times']
        price = options['price']
        rows = options['rows']
        cols = options['cols']

        if times_arg:
            times = []
            for t in times_arg.split(','):
                t = t.strip()
                try:
                    hh, mm = t.split(':')
                    times.append(time(int(hh), int(mm)))
                except Exception:
                    self.stdout.write(self.style.WARNING(f"Skipping invalid time: {t}"))
            if not times:
                times = DEFAULT_TIMES
        else:
            times = DEFAULT_TIMES

        # Choose movies to rotate through. Prefer running movies; fallback to any movie.
        movies_qs = Movie.objects.filter(status='running').order_by('release_date')
        if not movies_qs.exists():
            movies_qs = Movie.objects.all().order_by('release_date')

        movies = list(movies_qs)
        if not movies:
            self.stdout.write(self.style.ERROR('No movies found in database. Create movies first.'))
            return

        row_labels = [chr(ord('A') + i) for i in range(rows)]

        with transaction.atomic():
            theatres = Theatre.objects.all()
            movie_index = 0
            for theatre in theatres:
                for screen in theatre.screens.all():
                    # Ensure seats exist
                    existing = screen.seats.count()
                    needed = rows * cols
                    if existing < needed:
                        to_create = []
                        for r in row_labels:
                            for c in range(1, cols + 1):
                                to_create.append(Seat(
                                    screen=screen,
                                    row=r,
                                    seat_number=c,
                                    seat_type='standard',
                                    is_available=True,
                                    status='available',
                                    base_price=price
                                ))
                        Seat.objects.bulk_create(to_create)
                        self.stdout.write(self.style.SUCCESS(f'Created {len(to_create)} seats for {screen}'))
                    else:
                        self.stdout.write(self.style.NOTICE(f'{screen} already has {existing} seats'))

                    # Create shows for next N days at given times
                    for day_offset in range(days):
                        show_date = (datetime.now().date() + timedelta(days=day_offset))
                        for t in times:
                            show_time = t
                            movie = movies[movie_index % len(movies)]
                            # Avoid duplicates: show with same movie/screen/date/time
                            exists = Show.objects.filter(
                                screen=screen,
                                movie=movie,
                                show_date=show_date,
                                show_time=show_time
                            ).exists()
                            if exists:
                                self.stdout.write(self.style.NOTICE(f'Show already exists: {screen} {movie.title} {show_date} {show_time}'))
                                movie_index += 1
                                continue

                            # Calculate end_time from movie duration
                            try:
                                duration = getattr(movie, 'duration_minutes', None) or 120
                                dt = datetime.combine(show_date, show_time) + timedelta(minutes=int(duration))
                                end_time = dt.time()
                            except Exception:
                                end_time = (datetime.combine(show_date, show_time) + timedelta(minutes=120)).time()

                            Show.objects.create(
                                screen=screen,
                                movie=movie,
                                show_date=show_date,
                                show_time=show_time,
                                end_time=end_time,
                                base_ticket_price=price,
                                status='available',
                                is_active=True
                            )
                            self.stdout.write(self.style.SUCCESS(f'Created show: {screen} - {movie.title} on {show_date} at {show_time}'))

                            movie_index += 1

        self.stdout.write(self.style.SUCCESS('Show seeding complete'))
