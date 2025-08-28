"""Test redirect Location header handling with special characters"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        ROOT_URLCONF='test_urls',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
    )
    django.setup()

from django.shortcuts import redirect

# Test various URLs with special characters
test_cases = [
    "./test",
    "../test",
    "./€",
    "../€",
    "./\x00",  # Null byte
    "../\x00",
    "./\n",    # Newline
    "../\n",
    "/test\nSet-Cookie: evil=true",  # Header injection attempt
    "/test\r\nSet-Cookie: evil=true", # CRLF injection attempt
]

print("Testing redirect Location header handling:")
print("-" * 50)

for url in test_cases:
    try:
        response = redirect(url)
        location = response["Location"]
        
        # Check if location has been escaped/encoded
        if location != url:
            print(f"MODIFIED: redirect({url!r}) -> Location: {location!r}")
        else:
            print(f"UNCHANGED: redirect({url!r}) -> Location: {location!r}")
        
        # Check for potential header injection
        if "\n" in location or "\r" in location:
            print(f"  WARNING: Location contains newline characters!")
            
    except Exception as e:
        print(f"ERROR: redirect({url!r}) raised {e.__class__.__name__}: {e}")

# Test with actual Unicode that needs IRI to URI conversion
print("\nTesting IRI to URI conversion:")
print("-" * 50)

iri_tests = [
    "http://example.com/€",
    "https://example.com/test with spaces",
    "/path/with spaces",
    "./path with spaces",
    "../path with spaces",
]

for url in iri_tests:
    response = redirect(url)
    location = response["Location"]
    print(f"redirect({url!r})")
    print(f"  Location: {location!r}")
    if location != url:
        print(f"  (converted from IRI to URI)")