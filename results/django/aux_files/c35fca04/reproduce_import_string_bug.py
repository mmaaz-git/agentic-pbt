"""
Investigate import_string error handling behavior
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
)
django.setup()

from django.db.utils import import_string

# Test case 1: Module not found
print("Test 1: Module not found")
try:
    import_string('0.')
except Exception as e:
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {e}")
    print(f"Is ImportError: {isinstance(e, ImportError)}")
    print()

# Test case 2: Invalid format
print("Test 2: Invalid format (no dot)")
try:
    import_string('nodot')
except Exception as e:
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {e}")
    print(f"Is ImportError: {isinstance(e, ImportError)}")
    print()

# Test case 3: Valid module but missing attribute
print("Test 3: Valid module but missing attribute")
try:
    import_string('os.nonexistent')
except Exception as e:
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {e}")
    print(f"Is ImportError: {isinstance(e, ImportError)}")