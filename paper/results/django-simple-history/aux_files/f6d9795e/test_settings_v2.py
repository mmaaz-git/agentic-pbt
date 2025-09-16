
import os
import sys

SECRET_KEY = 'test-secret-key'
DEBUG = True

# Add current directory to path for test_app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'simple_history',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

USE_TZ = True
TIME_ZONE = 'UTC'

# Simplify middleware for testing
MIDDLEWARE = []
