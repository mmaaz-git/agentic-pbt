#!/usr/bin/env python3
"""Investigate how transform_field is actually used in the codebase"""

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

from simple_history.models import HistoricalRecords, transform_field
import copy

print("Investigating the actual usage context of transform_field...")
print("="*60)

# Let's trace how transform_field is called in the actual code flow
class TestModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    class Meta:
        app_label = 'test'

print("Created TestModel with HistoricalRecords")

# Let's look at how copy_fields works (which calls transform_field)
hr = TestModel.history
fields_to_copy = hr.fields_included(TestModel)

print(f"\nFields to be copied for history: {[f.name for f in fields_to_copy]}")

# Simulate what copy_fields does
print("\nSimulating copy_fields process:")
for field in fields_to_copy:
    print(f"\n  Processing field: {field.name}")
    print(f"    Original type: {field.__class__.__name__}")
    print(f"    Has attname: {hasattr(field, 'attname')}")
    
    # This is what copy_fields does
    field_copy = copy.copy(field)
    print(f"    After copy, has attname: {hasattr(field_copy, 'attname')}")
    
    # The key insight: copy.copy preserves the attname attribute
    if hasattr(field_copy, 'attname'):
        print(f"    attname value: {field_copy.attname}")
    
    # Now transform it
    try:
        transform_field(field_copy)
        print(f"    ✓ Transform succeeded -> {field_copy.__class__.__name__}")
    except AttributeError as e:
        print(f"    ✗ Transform failed: {e}")

print("\n" + "="*60)
print("\nKey finding:")
print("In the actual code flow, transform_field is called on fields")
print("that have been copied from a model's _meta.fields.")
print("These fields already have attname set, so the bug doesn't")
print("manifest in normal usage.")
print("\nHowever, the function is public and could be called")
print("in other contexts where attname might not exist.")

print("\n" + "="*60)
print("\nTesting edge case: What if someone tries to use transform_field")
print("directly on a newly created field?")

# This is a legitimate use case that could happen
new_field = models.CharField(max_length=100)
print(f"\nCreated new CharField")
print(f"Has attname: {hasattr(new_field, 'attname')}")

try:
    transform_field(new_field)
    print("✓ transform_field succeeded")
except AttributeError as e:
    print(f"✗ transform_field failed: {e}")
    print("\nThis confirms the bug exists for direct usage")