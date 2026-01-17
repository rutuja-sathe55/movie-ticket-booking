from django.core.management.base import BaseCommand
from decouple import config
import razorpay
from razorpay.errors import BadRequestError

class Command(BaseCommand):
    help = 'Validate Razorpay API keys in .env by making a lightweight API call'

    def handle(self, *args, **options):
        key = config('RAZORPAY_KEY_ID', default='').strip()
        secret = config('RAZORPAY_KEY_SECRET', default='').strip()
        if not key or not secret:
            self.stdout.write(self.style.ERROR('RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET not set in environment'))
            return
        self.stdout.write(f'Using RAZORPAY_KEY_ID={key}')
        try:
            client = razorpay.Client(auth=(key, secret))
            try:
                res = client.order.all({'count': 1})
                self.stdout.write(self.style.SUCCESS('Authentication succeeded. API call returned:'))
                self.stdout.write(str(res))
            except BadRequestError as e:
                self.stdout.write(self.style.ERROR(f'Authentication failed: {e}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'API call failed with error: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create Razorpay client: {e}'))
