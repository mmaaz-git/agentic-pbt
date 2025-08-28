#!/usr/bin/env python3
"""
Minimal reproduction of IndexError bug in AppConfig.create
"""

import django
from django.conf import settings
from django.apps import AppConfig

# Configure minimal Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    INSTALLED_APPS=[],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
django.setup()

print("Testing AppConfig.create with trailing dot...")
print("Input: 'django.contrib.auth.'")

try:
    config = AppConfig.create('django.contrib.auth.')
    print(f"Result: {config}")
except IndexError as e:
    print(f"IndexError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Other error: {e}")

print("\n" + "="*50)
print("Testing with double trailing dots...")
print("Input: 'django.contrib.auth..'")

try:
    config = AppConfig.create('django.contrib.auth..')
    print(f"Result: {config}")
except IndexError as e:
    print(f"IndexError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Other error: {e}")