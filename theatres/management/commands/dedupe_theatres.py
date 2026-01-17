from django.core.management.base import BaseCommand
from django.db import transaction
from theatres.models import Theatre, Screen, Seat

class Command(BaseCommand):
    help = 'Merge duplicate theatres (same name+city). Keep lowest-id theatre. Optionally remove generic Pune Theatre 1..5.'

    def add_arguments(self, parser):
        parser.add_argument('--city', type=str, help='If provided, limit generic removal to this city')
        parser.add_argument('--remove-generic', action='store_true', help='Remove generic "<City> Theatre 1..5" theatres')

    def handle(self, *args, **options):
        city_filter = options.get('city')
        remove_generic = options.get('remove_generic')

        with transaction.atomic():
            # 1) Merge duplicates grouped by (name, city)
            self.stdout.write('Scanning for duplicate theatres...')
            from django.db.models import Count
            duplicates = (Theatre.objects.values('name', 'city')
                          .annotate(cnt=Count('id'))
                          .filter(cnt__gt=1))

            for grp in duplicates:
                name = grp['name']
                city = grp['city']
                qs = Theatre.objects.filter(name=name, city=city).order_by('id')
                keeper = qs.first()
                others = qs.exclude(id=keeper.id)
                self.stdout.write(self.style.NOTICE(f"Merging {qs.count()} theatres for {name} ({city}) -> keeping id={keeper.id}"))

                for other in others:
                    # Move screens from other to keeper, handling name collisions
                    for screen in list(other.screens.all()):
                        existing = Screen.objects.filter(theatre=keeper, name=screen.name).first()
                        if existing:
                            # move seats: avoid duplicates
                            for seat in list(screen.seats.all()):
                                if existing.seats.filter(row=seat.row, seat_number=seat.seat_number).exists():
                                    # Seat already exists on destination; remove duplicate seat
                                    seat.delete()
                                else:
                                    seat.screen = existing
                                    seat.save()
                            # delete the now-empty screen
                            screen.delete()
                            self.stdout.write(self.style.NOTICE(f"Merged seats from screen '{screen.name}' into existing screen on keeper theatre"))
                        else:
                            # safe to reassign the screen to keeper
                            screen.theatre = keeper
                            screen.save()
                            self.stdout.write(self.style.NOTICE(f"Moved screen '{screen.name}' to keeper theatre id={keeper.id}"))

                    # After moving screens, delete the duplicate theatre record
                    other.delete()
                    self.stdout.write(self.style.SUCCESS(f"Deleted duplicate theatre id={other.id} ({name}, {city})"))

            # 2) Optionally remove generic theatres like 'Pune Theatre 1'..'Pune Theatre 5'
            if remove_generic:
                cities = [city_filter] if city_filter else set(Theatre.objects.values_list('city', flat=True))
                for city in cities:
                    for i in range(1, 6):
                        generic_name = f"{city} Theatre {i}"
                        qs = Theatre.objects.filter(name=generic_name, city=city)
                        if not qs.exists():
                            continue
                        # If there is more than one, delete them all (they're generic duplicates)
                        count = qs.count()
                        # Before deleting, move any screens to a sensible target if possible: find another theatre in same city with similar name
                        # We'll attempt to move screens to the first non-generic theatre in this city, if present
                        dest = Theatre.objects.filter(city=city).exclude(name__startswith=f"{city} Theatre").first()
                        for th in qs:
                            if dest:
                                for screen in list(th.screens.all()):
                                    # if dest has same screen name, try to merge seats
                                    existing = Screen.objects.filter(theatre=dest, name=screen.name).first()
                                    if existing:
                                        for seat in list(screen.seats.all()):
                                            if existing.seats.filter(row=seat.row, seat_number=seat.seat_number).exists():
                                                seat.delete()
                                            else:
                                                seat.screen = existing
                                                seat.save()
                                        screen.delete()
                                    else:
                                        screen.theatre = dest
                                        screen.save()
                                th.delete()
                                self.stdout.write(self.style.SUCCESS(f"Removed generic theatre '{th.name}' and moved screens to '{dest.name}'"))
                            else:
                                # no sensible destination — delete (cascades will remove screens/seats)
                                th.delete()
                                self.stdout.write(self.style.SUCCESS(f"Deleted generic theatre '{th.name}' (no destination available)"))
                        self.stdout.write(self.style.SUCCESS(f"Processed {count} generic theatres named '{generic_name}' in {city}"))

        self.stdout.write(self.style.SUCCESS('Deduplication complete'))
