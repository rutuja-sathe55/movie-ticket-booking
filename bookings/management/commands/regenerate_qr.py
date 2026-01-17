"""
Management command to regenerate QR codes for all tickets.
Use this when QR data or images need to be updated (e.g., after model changes).
"""

from django.core.management.base import BaseCommand
from bookings.models import Ticket


class Command(BaseCommand):
    help = 'Regenerate QR codes and data for all tickets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate QR for all tickets (default: only missing QR)',
        )

    def handle(self, *args, **options):
        regenerate_all = options.get('all', False)

        if regenerate_all:
            tickets = Ticket.objects.all()
            self.stdout.write(f'Regenerating QR for all {tickets.count()} tickets...')
        else:
            tickets = Ticket.objects.filter(qr_code='')
            self.stdout.write(f'Regenerating QR for {tickets.count()} tickets with missing QR images...')

        count = 0
        for ticket in tickets:
            try:
                # Force regeneration by clearing and re-setting
                if regenerate_all:
                    ticket.qr_data = ''
                    ticket.qr_code = None

                # Save will trigger QR generation if needed
                ticket.save()
                count += 1
                self.stdout.write(f'  ✓ Ticket {ticket.ticket_id}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error for Ticket {ticket.ticket_id}: {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully regenerated {count} QR codes!'))
