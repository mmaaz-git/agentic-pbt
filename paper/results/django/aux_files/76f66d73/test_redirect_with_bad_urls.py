"""Test redirect with objects returning bad URLs from get_absolute_url"""

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

from django.shortcuts import redirect, resolve_url


class ModelReturningNone:
    """Model with get_absolute_url returning None"""
    def get_absolute_url(self):
        return None


class ModelReturningInt:
    """Model with get_absolute_url returning integer"""  
    def get_absolute_url(self):
        return 12345


class ModelReturningList:
    """Model with get_absolute_url returning list"""
    def get_absolute_url(self):
        return ["/url1", "/url2"]


# Test with None
print("Testing redirect with model returning None from get_absolute_url:")
model = ModelReturningNone()
try:
    # First check what resolve_url returns
    resolved = resolve_url(model)
    print(f"resolve_url returned: {resolved!r} (type: {type(resolved).__name__})")
    
    # Now try redirect
    response = redirect(model)
    print(f"redirect succeeded, Location: {response['Location']!r}")
except Exception as e:
    print(f"redirect raised {e.__class__.__name__}: {e}")

# Test with integer
print("\nTesting redirect with model returning int from get_absolute_url:")
model = ModelReturningInt()
try:
    resolved = resolve_url(model)
    print(f"resolve_url returned: {resolved!r} (type: {type(resolved).__name__})")
    
    response = redirect(model)
    print(f"redirect succeeded, Location: {response['Location']!r}")
except Exception as e:
    print(f"redirect raised {e.__class__.__name__}: {e}")

# Test with list
print("\nTesting redirect with model returning list from get_absolute_url:")
model = ModelReturningList()
try:
    resolved = resolve_url(model)
    print(f"resolve_url returned: {resolved!r} (type: {type(resolved).__name__})")
    
    response = redirect(model)
    print(f"redirect succeeded, Location: {response['Location']!r}")
except Exception as e:
    print(f"redirect raised {e.__class__.__name__}: {e}")