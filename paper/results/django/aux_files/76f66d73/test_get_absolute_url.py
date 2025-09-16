"""Test resolve_url with objects having get_absolute_url"""

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


class ModelWithGetAbsoluteUrl:
    """Model that has get_absolute_url method"""
    def __init__(self, url):
        self.url = url
    
    def get_absolute_url(self):
        return self.url


class ModelWithBrokenGetAbsoluteUrl:
    """Model with get_absolute_url that raises exception"""
    def get_absolute_url(self):
        raise ValueError("Broken get_absolute_url")


class ModelReturningNone:
    """Model with get_absolute_url returning None"""
    def get_absolute_url(self):
        return None


class ModelReturningNonString:
    """Model with get_absolute_url returning non-string"""
    def get_absolute_url(self):
        return 12345


# Test normal case
print("Testing normal get_absolute_url:")
model = ModelWithGetAbsoluteUrl("/my/url/")
result = resolve_url(model)
print(f"resolve_url(model with url='/my/url/') -> {result!r}")

# Test with relative URLs
print("\nTesting get_absolute_url returning relative URLs:")
for url in ["./relative", "../parent", "/absolute"]:
    model = ModelWithGetAbsoluteUrl(url)
    result = resolve_url(model)
    print(f"resolve_url(model with url={url!r}) -> {result!r}")

# Test edge cases
print("\nTesting edge cases:")

# Empty string
model = ModelWithGetAbsoluteUrl("")
result = resolve_url(model)
print(f"resolve_url(model with url='') -> {result!r}")

# None
model = ModelReturningNone()
try:
    result = resolve_url(model)
    print(f"resolve_url(model returning None) -> {result!r}")
except Exception as e:
    print(f"resolve_url(model returning None) raised {e.__class__.__name__}: {e}")

# Non-string
model = ModelReturningNonString()
try:
    result = resolve_url(model)
    print(f"resolve_url(model returning 12345) -> {result!r}")
except Exception as e:
    print(f"resolve_url(model returning 12345) raised {e.__class__.__name__}: {e}")

# Exception in get_absolute_url
model = ModelWithBrokenGetAbsoluteUrl()
try:
    result = resolve_url(model)
    print(f"resolve_url(model with broken method) -> {result!r}")
except Exception as e:
    print(f"resolve_url(model with broken method) raised {e.__class__.__name__}: {e}")

# Test object that has both get_absolute_url and looks like a string
class StringLikeModel(str):
    """String subclass with get_absolute_url"""
    def __new__(cls, string_value, url):
        instance = super().__new__(cls, string_value)
        instance.url = url
        return instance
    
    def get_absolute_url(self):
        return self.url

print("\nTesting precedence - object with get_absolute_url that's also a string:")
model = StringLikeModel("/string/value", "/absolute/url")
result = resolve_url(model)
print(f"String value: {str(model)!r}")
print(f"get_absolute_url returns: {model.get_absolute_url()!r}")
print(f"resolve_url result: {result!r}")
if result == model.get_absolute_url():
    print("✓ get_absolute_url takes precedence over string value")
else:
    print("✗ String value used instead of get_absolute_url")