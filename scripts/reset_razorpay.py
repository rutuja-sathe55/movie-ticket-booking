# Script to reset payments stuck in 'processing' state to 'failed' and clear razorpay fields.
# Intended to be run via: python manage.py shell -c "exec(open('scripts/reset_razorpay.py').read())"
from payments.models import Payment
from django.utils import timezone

stale = Payment.objects.filter(status='processing')
print(f'Found {stale.count()} processing payments to reset')
for p in stale:
    print(f' - Resetting Payment id={p.pk} booking={p.booking_id} amount={p.total_amount}')
    p.status = 'failed'
    p.razorpay_order_id = None
    p.razorpay_payment_id = None
    p.razorpay_signature = None
    p.completed_at = None
    p.save()
print('Reset complete')
