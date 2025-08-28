"""Reproduce the cache versioning bug."""

import django
from django.conf import settings

# Configure Django settings with cache
if not settings.configured:
    settings.configure(
        SECRET_KEY='test-secret-key',
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }
    )

from django.core.cache import cache

# Clear cache
cache.clear()

# Reproduce the bug with minimal values
key = '0'
value = 0
version1 = 0
version2 = 0

print(f"Testing with key='{key}', value={value}, version1={version1}, version2={version2}")

# Set with version1
cache.set(key, value, version=version1)
print(f"Set cache['{key}'] = {value} with version={version1}")

# Get with same version should work
result1 = cache.get(key, version=version1)
print(f"Get cache['{key}'] with version={version1}: {result1}")

# This should equal value (0) but the test showed it equals 1
assert result1 == value, f"Expected {value}, got {result1}"

# Set different value with version2 (same as version1 in this case)
value2 = value + 1  # value2 = 1
cache.set(key, value2, version=version2)
print(f"Set cache['{key}'] = {value2} with version={version2}")

# Get with version1 again
result2 = cache.get(key, version=version1)
print(f"Get cache['{key}'] with version={version1}: {result2}")

# Since version1 == version2, this should now return value2 (1)
# But the original test expected it to still return value (0)
print(f"\nExpected behavior: When version1 == version2, setting with version2 should overwrite version1")
print(f"Result: cache.get(key, version={version1}) = {result2} (should be {value2} since versions are the same)")