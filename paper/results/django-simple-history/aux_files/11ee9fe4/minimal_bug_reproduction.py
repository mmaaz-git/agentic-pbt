#!/usr/bin/env python3
"""Minimal reproduction of the transform_field bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

# Minimal Django setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

from django.conf import settings
if not settings.configured:
    settings.configure(
        SECRET_KEY='test',
        INSTALLED_APPS=['django.contrib.contenttypes'],
    )

import django
django.setup()

from django.db import models
from simple_history.models import transform_field

print("Minimal Bug Reproduction")
print("="*60)

# Create a field without attaching it to a model
# This is a valid Django field object
field = models.CharField(max_length=100)

print(f"Created CharField")
print(f"Field has 'attname': {hasattr(field, 'attname')}")
print(f"Field has 'name': {hasattr(field, 'name')}")

print("\nCalling transform_field()...")

try:
    transform_field(field)
    print("SUCCESS: No error occurred")
except AttributeError as e:
    print(f"BUG CONFIRMED: AttributeError - {e}")
    print("\nStack trace shows the error occurs at:")
    print("  simple_history/models.py:821")
    print("  field.name = field.attname")
    print("\nThe function assumes 'attname' exists, but it doesn't")
    print("for fields not attached to a model.")

print("\n" + "="*60)
print("\nWhy this is a bug:")
print("1. transform_field is a module-level function (not a method)")
print("2. It's defined at the module level, suggesting it could be")
print("   used independently")
print("3. It fails on valid Django field objects that aren't")
print("   attached to models")
print("4. The fix is simple: check if attname exists before using it")