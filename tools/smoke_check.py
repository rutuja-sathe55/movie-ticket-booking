"""
Simple smoke test script for local Django dev server
Run: python tools/smoke_check.py
"""
import requests

BASE = "http://127.0.0.1:8000"
ENDPOINTS = [
    "/",
    "/movies/",
    "/movies/coming-soon/",
    "/theatres/",
    "/theatres/1/",
    "/food/menu/",
    "/bookings/",
    "/admin/",
]

results = []
for path in ENDPOINTS:
    url = BASE + path
    try:
        r = requests.get(url, allow_redirects=False, timeout=5)
        results.append((path, r.status_code))
    except Exception as e:
        results.append((path, f"ERROR: {e}"))

for path, status in results:
    print(f"{path} -> {status}")

# Simple exit code: non-zero if any endpoint errored (not including expected redirects)
errors = [s for p, s in results if isinstance(s, str) and s.startswith('ERROR')]
bad = [s for p, s in results if isinstance(s, int) and s >= 500]
if errors or bad:
    print("Smoke check: FAIL")
    raise SystemExit(1)
print("Smoke check: PASS")
