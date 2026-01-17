from django.core.management.base import BaseCommand
from theatres.models import Theatre, Screen, Seat
from django.db import transaction


REAL_THEATRES = {
    'Pune': [
        {
            'name': 'PVR Phoenix Marketcity',
            'address': 'Phoenix Marketcity, Viman Nagar',
            'phone_number': '020-66890000',
            'email': 'pvr.pune@pvrcinemas.com',
            'latitude': 18.5610,
            'longitude': 73.9145,
            'has_4k': True,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'INOX Amanora',
            'address': 'Amanora Mall, Hadapsar',
            'phone_number': '020-71110000',
            'email': 'inox.amanora@example.com',
            'latitude': 18.5204,
            'longitude': 73.9142,
            'has_4k': True,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'Cinepolis Seasons Mall',
            'address': 'Seasons Mall, Pashan Road',
            'phone_number': '020-66550000',
            'email': 'cinepolis.seasons@example.com',
            'latitude': 18.5205,
            'longitude': 73.8410,
            'has_4k': False,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'PVR Koregaon Park',
            'address': 'Koregaon Park',
            'phone_number': '020-66000000',
            'email': 'pvr.koregaon@example.com',
            'latitude': 18.5360,
            'longitude': 73.8887,
            'has_4k': True,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'Cinepolis Phoenix Marketcity (Pune)',
            'address': 'Phoenix Marketcity, Viman Nagar',
            'phone_number': '020-66890001',
            'email': 'cinepolis.pune@example.com',
            'latitude': 18.5609,
            'longitude': 73.9146,
            'has_4k': True,
            'has_imax': False,
            'has_dolby': True,
        },
    ],
    'Mumbai': [
        {
            'name': 'INOX R-City Ghatkopar',
            'address': 'R-City Mall, Ghatkopar West',
            'phone_number': '022-66439999',
            'email': 'inox.mumbai@inoxmovies.com',
            'latitude': 19.0990,
            'longitude': 72.9165,
            'has_4k': True,
            'has_imax': True,
            'has_dolby': True,
        },
        {
            'name': 'PVR Juhu',
            'address': 'Juhu Tara Road',
            'phone_number': '022-66000001',
            'email': 'pvr.juhu@example.com',
            'latitude': 19.0986,
            'longitude': 72.8266,
            'has_4k': True,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'Cinepolis Inorbit Malad',
            'address': 'Inorbit Mall, Malad',
            'phone_number': '022-66000002',
            'email': 'cinepolis.malad@example.com',
            'latitude': 19.1850,
            'longitude': 72.8466,
            'has_4k': False,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'PVR Phoenix Mills',
            'address': 'Phoenix Mills, Lower Parel',
            'phone_number': '022-66000003',
            'email': 'pvr.phoenix@example.com',
            'latitude': 19.0188,
            'longitude': 72.8290,
            'has_4k': True,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'INOX Versova',
            'address': 'Versova, Andheri West',
            'phone_number': '022-66000004',
            'email': 'inox.versova@example.com',
            'latitude': 19.1506,
            'longitude': 72.8209,
            'has_4k': False,
            'has_imax': False,
            'has_dolby': True,
        },
    ],
    'Nashik': [
        {
            'name': 'Cinepolis City Centre',
            'address': 'City Centre Mall, College Road',
            'phone_number': '0253-2300000',
            'email': 'cinepolis.nashik@cinepolis.com',
            'latitude': 19.9975,
            'longitude': 73.7898,
            'has_4k': False,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'PVR Nashik',
            'address': 'PVR Complex, Nashik Road',
            'phone_number': '0253-6600000',
            'email': 'pvr.nashik@example.com',
            'latitude': 19.9970,
            'longitude': 73.7900,
            'has_4k': True,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'Fame Cinemas Nashik',
            'address': 'Fame Mall, Nashik',
            'phone_number': '0253-6600001',
            'email': 'fame.nashik@example.com',
            'latitude': 19.9980,
            'longitude': 73.7880,
            'has_4k': False,
            'has_imax': False,
            'has_dolby': False,
        },
        {
            'name': 'Inox Panchavati',
            'address': 'Panchavati Complex',
            'phone_number': '0253-6600002',
            'email': 'inox.panchavati@example.com',
            'latitude': 20.0020,
            'longitude': 73.7905,
            'has_4k': False,
            'has_imax': False,
            'has_dolby': True,
        },
        {
            'name': 'City Pride Nashik',
            'address': 'Central City Mall',
            'phone_number': '0253-6600003',
            'email': 'citypride.nashik@example.com',
            'latitude': 19.9950,
            'longitude': 73.7920,
            'has_4k': False,
            'has_imax': False,
            'has_dolby': False,
        },
    ]
}


class Command(BaseCommand):
    help = 'Seed realistic theatres: 5 theatres per city, each with 2 screens and 100 seats per screen'

    def add_arguments(self, parser):
        parser.add_argument('--cities', nargs='+', default=['Pune', 'Mumbai', 'Nashik'], help='List of cities to seed')
        parser.add_argument('--screens-per-theatre', type=int, default=2)
        parser.add_argument('--rows', type=int, default=10)
        parser.add_argument('--cols', type=int, default=10)
        parser.add_argument('--price', type=int, default=200)
        parser.add_argument('--use-real', action='store_true', help='Use built-in realistic theatre data')

    def handle(self, *args, **options):
        cities = options['cities']
        screens_per_theatre = options['screens_per_theatre']
        rows = options['rows']
        cols = options['cols']
        price = options['price']
        use_real = options['use_real']

        row_labels = [chr(ord('A') + i) for i in range(rows)]

        with transaction.atomic():
            for city in cities:
                theatres_list = REAL_THEATRES.get(city, []) if use_real else []

                # If real list is shorter than 5, fallback to generic naming for remaining
                if use_real and theatres_list:
                    chosen = theatres_list
                else:
                    # generic 5 theatres
                    chosen = [{'name': f"{city} Theatre {i}", 'address': f"{city} Theatre {i} Address",
                               'phone_number': '0000000000', 'email': f"theatre{i}.{city.lower()}@example.com",
                               'latitude': None, 'longitude': None,
                               'has_4k': False, 'has_imax': False, 'has_dolby': False}
                              for i in range(1, 6)]

                for tinfo in chosen:
                    name = tinfo['name']
                    theatre, created = Theatre.objects.get_or_create(
                        name=name,
                        defaults={
                            'address': tinfo.get('address', ''),
                            'city': city,
                            'state': tinfo.get('state', 'State'),
                            'postal_code': tinfo.get('postal_code', '000000'),
                            'phone_number': tinfo.get('phone_number', '0000000000'),
                            'email': tinfo.get('email', f"{name.replace(' ', '').lower()}@example.com"),
                            'total_screens': screens_per_theatre,
                            'is_active': True,
                            'has_4k': tinfo.get('has_4k', False),
                            'has_imax': tinfo.get('has_imax', False),
                            'has_dolby': tinfo.get('has_dolby', False),
                            'latitude': tinfo.get('latitude'),
                            'longitude': tinfo.get('longitude'),
                        }
                    )

                    for s_i in range(1, screens_per_theatre + 1):
                        screen_name = f"Screen {s_i}"
                        screen, s_created = Screen.objects.get_or_create(
                            theatre=theatre,
                            name=screen_name,
                            defaults={
                                'capacity': rows * cols,
                                'total_rows': rows,
                                'seats_per_row': cols,
                                'is_active': True,
                            }
                        )

                        existing = screen.seats.count()
                        if existing >= rows * cols:
                            self.stdout.write(self.style.NOTICE(f"{screen} already has {existing} seats, skipping"))
                            continue

                        seats_to_create = []
                        for r_label in row_labels:
                            for c in range(1, cols + 1):
                                seats_to_create.append(Seat(
                                    screen=screen,
                                    row=r_label,
                                    seat_number=c,
                                    seat_type='standard',
                                    is_available=True,
                                    status='available',
                                    base_price=price
                                ))

                        Seat.objects.bulk_create(seats_to_create)
                        self.stdout.write(self.style.SUCCESS(f"Created {len(seats_to_create)} seats for {screen}"))

            self.stdout.write(self.style.SUCCESS('Seeding complete'))
