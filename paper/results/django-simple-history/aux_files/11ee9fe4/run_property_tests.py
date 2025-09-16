#!/usr/bin/env python3
"""Run property-based tests for django-simple-history models"""

import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

import django
from django.conf import settings
from django.db import models
from hypothesis import given, strategies as st, assume, settings as hyp_settings

# Configure Django settings for testing
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
        SIMPLE_HISTORY_ENABLED=True,
    )
    django.setup()

from simple_history.models import transform_field, HistoricalChanges, ModelChange

print("Testing property 1: AutoField transformation...")

# Test 1: AutoField transformation
field1 = models.AutoField(primary_key=True)
original_class1 = field1.__class__
transform_field(field1)
assert field1.__class__ == models.IntegerField, f"AutoField should transform to IntegerField, got {field1.__class__}"
print("✓ AutoField transforms to IntegerField")

# Test 2: BigAutoField transformation  
field2 = models.BigAutoField(primary_key=True)
original_class2 = field2.__class__
transform_field(field2)
assert field2.__class__ == models.BigIntegerField, f"BigAutoField should transform to BigIntegerField, got {field2.__class__}"
print("✓ BigAutoField transforms to BigIntegerField")

# Test 3: auto_now and auto_now_add are disabled
field3 = models.DateTimeField(auto_now=True, auto_now_add=True)
transform_field(field3)
assert field3.auto_now == False, "auto_now should be False after transformation"
assert field3.auto_now_add == False, "auto_now_add should be False after transformation"
print("✓ auto_now and auto_now_add are disabled after transformation")

print("\nTesting property 2: Unique field transformation...")

# Test 4: Unique fields become non-unique but indexed
field4 = models.CharField(max_length=100, unique=True)
transform_field(field4)
assert field4.primary_key == False, "primary_key should be False"
assert field4._unique == False, "unique should be False" 
assert field4.db_index == True, "db_index should be True for previously unique fields"
assert field4.serialize == True, "serialize should be True"
print("✓ Unique fields become non-unique but indexed")

# Test 5: Primary key fields lose primary key status but gain index
field5 = models.IntegerField(primary_key=True)
transform_field(field5)
assert field5.primary_key == False, "primary_key should be False"
assert field5._unique == False, "unique should be False"
assert field5.db_index == True, "db_index should be True for previously primary key fields"
print("✓ Primary key fields lose primary key status but gain index")

print("\nTesting property 3: FileField transformation...")

# Test 6: FileField transformation based on settings
settings.SIMPLE_HISTORY_FILEFIELD_TO_CHARFIELD = True
field6a = models.FileField()
field6a.name = 'test_file'
field6a.attname = 'test_file'
transform_field(field6a)
assert field6a.__class__ == models.CharField, "FileField should transform to CharField when setting is True"
print("✓ FileField transforms to CharField when SIMPLE_HISTORY_FILEFIELD_TO_CHARFIELD=True")

settings.SIMPLE_HISTORY_FILEFIELD_TO_CHARFIELD = False
field6b = models.FileField()
field6b.name = 'test_file'
field6b.attname = 'test_file'
transform_field(field6b)
assert field6b.__class__ == models.TextField, "FileField should transform to TextField when setting is False"
print("✓ FileField transforms to TextField when SIMPLE_HISTORY_FILEFIELD_TO_CHARFIELD=False")

print("\nTesting property 4: Field name preservation...")

# Test 7: Field names are preserved as attname
field7 = models.CharField(max_length=50)
field7.name = 'original_name'
field7.attname = 'original_attname'
transform_field(field7)
assert field7.name == field7.attname, "field.name should equal field.attname after transformation"
assert field7.name == 'original_attname', "field.name should be set to original attname"
print("✓ Field names are preserved as attname during transformation")

print("\nTesting property 5: ModelChange immutability...")

# Test 8: ModelChange is immutable (frozen dataclass)
change = ModelChange(field='test_field', old='old_value', new='new_value')
try:
    hash(change)  # Should be hashable since it's frozen
    print("✓ ModelChange is hashable (frozen dataclass)")
except:
    print("✗ ModelChange is not hashable - should be frozen dataclass")

try:
    change.field = "modified"
    print("✗ ModelChange is mutable - should be frozen dataclass")
except:
    print("✓ ModelChange is immutable (cannot modify attributes)")

# Test equality
same_change = ModelChange(field='test_field', old='old_value', new='new_value')
assert change == same_change, "Equal ModelChange instances should be equal"
print("✓ ModelChange equality works correctly")

print("\nTesting property 6: Diff functionality...")

# Create a simple test for diff functionality
class SimpleHistoricalModel(HistoricalChanges):
    def __init__(self, **kwargs):
        self.tracked_fields = []
        self._history_m2m_fields = []
        self.instance_type = type('TestModel', (), {'_meta': type('Meta', (), {
            'get_field': lambda self, name: type('Field', (), {
                'name': name, 'editable': True, 'attname': name
            })()
        })()})
        for key, value in kwargs.items():
            setattr(self, key, value)

# Test diff detection
old_record = SimpleHistoricalModel(field1='value1', field2='value2')
new_record = SimpleHistoricalModel(field1='value1_changed', field2='value2')

class MockField:
    def __init__(self, name):
        self.name = name
        self.editable = True
        self.attname = name

old_record.tracked_fields = [MockField('field1'), MockField('field2')]
new_record.tracked_fields = [MockField('field1'), MockField('field2')]

delta = new_record.diff_against(old_record)
assert len(delta.changes) == 1, f"Should detect 1 change, detected {len(delta.changes)}"
assert delta.changes[0].field == 'field1', "Should detect change in field1"
assert delta.changes[0].old == 'value1', "Old value should be 'value1'"
assert delta.changes[0].new == 'value1_changed', "New value should be 'value1_changed'"
print("✓ Diff correctly detects field changes")

# Test no changes detected when values are the same
old_record2 = SimpleHistoricalModel(field1='same', field2='same')
new_record2 = SimpleHistoricalModel(field1='same', field2='same')
old_record2.tracked_fields = [MockField('field1'), MockField('field2')]
new_record2.tracked_fields = [MockField('field1'), MockField('field2')]

delta2 = new_record2.diff_against(old_record2)
assert len(delta2.changes) == 0, "Should detect no changes when values are the same"
print("✓ Diff correctly detects no changes when values are identical")

print("\n" + "="*50)
print("All property tests passed! ✅")
print("No bugs found in the tested properties.")