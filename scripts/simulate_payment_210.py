from decimal import Decimal
from django.utils import timezone
from payments.models import Payment

p = Payment.objects.filter(total_amount=Decimal('210.00')).first()
print('Found payment:', bool(p))
if p:
    import uuid
    p.razorpay_payment_id = 'SIMPAY' + uuid.uuid4().hex[:8].upper()
    p.razorpay_signature = 'SIMULATED_SIGNATURE'
    p.status = 'completed'
    p.completed_at = timezone.now()
    p.save()
    b = p.booking
    b.status = 'confirmed'
    b.payment_method = p.payment_method.get_name_display() if p.payment_method else 'online'
    b.save()
    print('Simulated payment for id', p.pk)
else:
    print('No payment with amount 210.00 found')