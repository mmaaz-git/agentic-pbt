#!/usr/bin/env python3
"""Test to reproduce the transform_field bug"""

import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

import django
from django.conf import settings
from django.db import models

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'simple_history',
        ],
        USE_TZ=True,
    )
    django.setup()

from simple_history.models import transform_field

print("Testing transform_field with fields that don't have attname...")
print("="*60)

# This is how fields are created when not attached to a model
# They don't have an attname attribute initially
field = models.AutoField(primary_key=True)

print(f"Field type: {field.__class__.__name__}")
print(f"Has 'attname' attribute: {hasattr(field, 'attname')}")
print(f"Has 'name' attribute: {hasattr(field, 'name')}")

if hasattr(field, 'name'):
    print(f"Field.name value: {field.name}")

print("\nAttempting to call transform_field...")

try:
    transform_field(field)
    print("✓ transform_field succeeded")
except AttributeError as e:
    print(f"✗ transform_field failed with AttributeError: {e}")
    print("\nThis is a BUG: transform_field assumes field.attname exists")
    print("but fields not attached to models don't have attname")
    
print("\n" + "="*60)
print("\nTesting with a field from an actual model...")

# Create a proper model with history tracking
class TestModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test'

# Now get the field from the model's _meta
model_field = TestModel._meta.get_field('id')

print(f"Model field type: {model_field.__class__.__name__}")
print(f"Has 'attname' attribute: {hasattr(model_field, 'attname')}")
print(f"Field.attname value: {model_field.attname}")
print(f"Field.name value: {model_field.name}")

print("\nAttempting to call transform_field on model's field...")

try:
    # Make a copy so we don't modify the actual model field
    import copy
    field_copy = copy.copy(model_field)
    transform_field(field_copy)
    print(f"✓ transform_field succeeded")
    print(f"  Transformed to: {field_copy.__class__.__name__}")
    print(f"  field.name after transform: {field_copy.name}")
except AttributeError as e:
    print(f"✗ transform_field failed: {e}")

print("\n" + "="*60)
print("\nBug Summary:")
print("The transform_field function in simple_history/models.py:821")
print("assumes that all fields have an 'attname' attribute.")
print("However, fields that are not attached to a model (e.g., when")
print("created directly) don't have this attribute, causing an")
print("AttributeError. This could affect programmatic field creation")
print("or testing scenarios.")