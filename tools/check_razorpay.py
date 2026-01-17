from decouple import config
import razorpay
import traceback

key = config('RAZORPAY_KEY_ID', default='')
secret = config('RAZORPAY_KEY_SECRET', default='')
print('RAZORPAY_KEY_ID=', key)
print('RAZORPAY_KEY_SECRET=', '***' if secret else '<empty>')
try:
    client = razorpay.Client(auth=(key, secret))
    print('Razorpay client created. Library version:', getattr(razorpay, '__version__', 'unknown'))
    print('Attempting to list orders (limit=1)')
    res = client.order.all({'count': 1})
    print('API call succeeded. Response:')
    print(res)
except Exception as e:
    print('API call raised exception:')
    traceback.print_exc()
