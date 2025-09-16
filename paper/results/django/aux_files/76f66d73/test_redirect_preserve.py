"""Test preserve_request parameter in redirect"""

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
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect


# Test basic functionality
response1 = redirect('/test/', preserve_request=False)
print(f"Response with preserve_request=False:")
print(f"  Type: {type(response1).__name__}")
print(f"  Status: {response1.status_code}")

response2 = redirect('/test/', preserve_request=True)
print(f"\nResponse with preserve_request=True:")
print(f"  Type: {type(response2).__name__}")
print(f"  Status: {response2.status_code}")

# According to Django docs, preserve_request should use status 307/308
# Let's check if preserve_request affects status code correctly
response3 = redirect('/test/', permanent=False, preserve_request=False)
response4 = redirect('/test/', permanent=False, preserve_request=True)
response5 = redirect('/test/', permanent=True, preserve_request=False)
response6 = redirect('/test/', permanent=True, preserve_request=True)

print("\nStatus code matrix:")
print(f"  permanent=False, preserve_request=False: {response3.status_code}")
print(f"  permanent=False, preserve_request=True: {response4.status_code}")
print(f"  permanent=True, preserve_request=False: {response5.status_code}")
print(f"  permanent=True, preserve_request=True: {response6.status_code}")

# Check the actual behavior mentioned in shortcut.py line 52
print("\nChecking preserve_request parameter passing...")
print(f"Line 52 passes preserve_request={True} to redirect_class")

# Let's look at HttpResponseRedirect to see if it accepts preserve_request
import inspect
print(f"\nHttpResponseRedirect signature: {inspect.signature(HttpResponseRedirect.__init__)}")