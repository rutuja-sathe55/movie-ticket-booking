"""
End-to-end booking flow tester (lightweight)
Run: python tools/e2e_booking.py
Requires the dev server running at http://127.0.0.1:8000
"""
import requests
from bs4 import BeautifulSoup

BASE = "http://127.0.0.1:8000"
S = requests.Session()

# 1. Find a show link from theatre detail
r = S.get(BASE + "/theatres/1/")
soup = BeautifulSoup(r.text, "html.parser")
show_link = None
# The app uses the URL pattern /show/<id>/seats/ (singular 'show'), so match that first
for a in soup.select("a[href*='/show/']"):
    show_link = a.get('href')
    break
# Fallback: look for Book Now buttons/links that mention 'seat' or have the seat_layout URL
if not show_link:
    for a in soup.find_all('a'):
        href = a.get('href') or ''
        if 'seat' in href or 'seats' in href:
            show_link = href
            break
if not show_link:
    print("No show link found on theatre page")
    raise SystemExit(1)
print("Found show link:", show_link)

# 2. Visit show page, pick first seat select form
r = S.get(BASE + show_link)
soup = BeautifulSoup(r.text, "html.parser")
# Find the seat selection form. Prefer a form with id 'seat-selection-form', else any form that contains
# a hidden input 'show_id' (used by the template to post to bookings:create_booking).
seat_form = soup.find('form', id='seat-selection-form')
if not seat_form:
    for f in soup.find_all('form'):
        if f.find('input', attrs={'name': 'show_id'}):
            seat_form = f
            break
if not seat_form:
    print('Seat selection form not found')
    raise SystemExit(1)

# 3. Simulate selecting one seat and posting
data = {}
# collect hidden/text inputs (e.g., show_id, discount)
for inp in seat_form.find_all('input'):
    if inp.get('type') in ('hidden', 'text'):
        data[inp.get('name')] = inp.get('value')
# seat inputs use class 'seat-checkbox' in the template
seats = soup.select("input[type=checkbox].seat-checkbox")
if not seats:
    # fallback to any checkbox in the form
    seats = seat_form.select("input[type=checkbox]")
if not seats:
    print('No seat checkboxes found')
    raise SystemExit(1)
seat_name = seats[0].get('name')
data[seat_name] = seats[0].get('value')

post_url = seat_form.get('action') or show_link
if not post_url.startswith('http'):
    post_url = BASE + post_url

r = S.post(post_url, data=data, allow_redirects=False)
print('Seat selection POST ->', r.status_code)
if r.status_code in (302, 303):
    print('Redirected to', r.headers.get('Location'))
else:
    print('Response length', len(r.text))

print('E2E script finished')
