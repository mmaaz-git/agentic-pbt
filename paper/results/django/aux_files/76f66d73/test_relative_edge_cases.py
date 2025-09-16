"""Test edge cases in relative URL handling"""

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

# Test various edge cases with relative URLs
test_cases = [
    "./",     # Simple relative current dir
    "../",    # Simple relative parent dir
    ".//",    # Double slash
    "..//",   # Double slash parent
    ".///",   # Triple slash
    "./\x00", # Null byte
    "../\x00",# Null byte parent
    "./\n",   # Newline
    "../\n",  # Newline parent
    "./\t",   # Tab
    "../\t",  # Tab parent
    "./ ",    # Space
    "../ ",   # Space parent
    "./.",    # Dot after slash
    "./..",   # Dot dot after slash
    "../.",   # Dot after parent
    "../..",  # Dot dot after parent
]

print("Testing relative URL edge cases:")
print("-" * 50)

for test in test_cases:
    result = resolve_url(test)
    if result != test:
        print(f"MISMATCH: resolve_url({test!r}) -> {result!r}")
    else:
        print(f"OK: resolve_url({test!r}) -> {result!r}")

# Special test: Unicode characters in relative URLs
unicode_tests = [
    "./€",
    "../€",
    "./😀",
    "../😀",
    "./\u200b",  # Zero-width space
    "../\u200b",
]

print("\nTesting Unicode in relative URLs:")
print("-" * 50)

for test in unicode_tests:
    result = resolve_url(test)
    if result != test:
        print(f"MISMATCH: resolve_url({test!r}) -> {result!r}")
    else:
        print(f"OK: resolve_url({test!r}) -> {result!r}")