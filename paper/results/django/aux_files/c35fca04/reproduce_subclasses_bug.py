"""
Minimal reproduction of the subclasses bug with object class
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
)
django.setup()

from django.db.models.query_utils import subclasses

# Test with object class
print("Testing subclasses(object):")
try:
    result = list(subclasses(object))
    print(f"Success: Found {len(result)} classes")
except TypeError as e:
    print(f"ERROR: {e}")
    print("This is a bug - subclasses() should handle the object class")

# Test with a normal class for comparison
print("\nTesting subclasses(int):")
try:
    result = list(subclasses(int))
    print(f"Success: Found {len(result)} classes")
    print(f"First item is int: {result[0] is int}")
except Exception as e:
    print(f"ERROR: {e}")