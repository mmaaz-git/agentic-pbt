"""Test empty string behavior in resolve_url"""

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

from django.shortcuts import resolve_url
from django.urls import NoReverseMatch

# Test empty string
print("Testing resolve_url('')...")
try:
    result = resolve_url("")
    print(f"Result: {result!r}")
except NoReverseMatch as e:
    print(f"NoReverseMatch raised: {e}")

# According to the code:
# Line 189-191: if "/" not in to and "." not in to: raise
# Empty string has neither "/" nor ".", so should raise
print("\nEmpty string contains '/':", "/" in "")
print("Empty string contains '.':", "." in "")
print("Expected behavior: Should raise NoReverseMatch")

# But what about single "/" or "."?
print("\nTesting resolve_url('/')...")
try:
    result = resolve_url("/")
    print(f"Result: {result!r}")
except NoReverseMatch as e:
    print(f"NoReverseMatch raised: {e}")

print("\nTesting resolve_url('.')...")
try:
    result = resolve_url(".")
    print(f"Result: {result!r}")
except NoReverseMatch as e:
    print(f"NoReverseMatch raised: {e}")