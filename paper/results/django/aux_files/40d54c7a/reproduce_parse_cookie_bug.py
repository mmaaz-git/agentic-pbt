import django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='test', DEFAULT_CHARSET='utf-8')

import django.http

# Demonstrate the bug: parse_cookie loses whitespace-only values
cookie_with_nbsp = "session_id=\xa0"
parsed = django.http.parse_cookie(cookie_with_nbsp)

print(f"Input cookie string: {repr(cookie_with_nbsp)}")
print(f"Parsed result: {parsed}")
print(f"Value for 'session_id': {repr(parsed['session_id'])}")
print()
print("Expected: {'session_id': '\\xa0'}")
print(f"Actual:   {{'session_id': {repr(parsed['session_id'])}}}")
print()
print("Bug: Non-breaking space value is lost, replaced with empty string")