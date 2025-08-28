#!/usr/bin/env python3
"""Minimal Django settings for testing"""

SECRET_KEY = 'test-secret-key-for-testing-only'
DEBUG = True
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'log_request_id',
]

MIDDLEWARE = [
    'log_request_id.middleware.RequestIDMiddleware',
]

ROOT_URLCONF = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

USE_TZ = True

# log_request_id specific settings
LOG_REQUEST_ID_HEADER = None
LOG_REQUESTS = False
NO_REQUEST_ID = 'none'
REQUEST_ID_RESPONSE_HEADER = None
GENERATE_REQUEST_ID_IF_NOT_IN_HEADER = False
LOG_USER_ATTRIBUTE = 'pk'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}