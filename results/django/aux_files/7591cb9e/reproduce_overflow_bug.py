"""Minimal reproduction of the was_modified_since overflow bug"""

import django
from django.conf import settings

# Configure Django
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test',
        USE_TZ=True,
        USE_I18N=True,
        INSTALLED_APPS=[],
        ROOT_URLCONF='',
    )

from django.views.static import was_modified_since
from django.utils.http import http_date, parse_http_date

# Test with the failing input
mtime = -2147483649  # Below 32-bit signed int minimum
header = http_date(1000000)

print(f"Testing was_modified_since with:")
print(f"  header: {header}")
print(f"  mtime: {mtime}")

result = was_modified_since(header, mtime)
print(f"  Result: {result}")
print(f"  Expected: True (due to overflow)")

# Let's trace through the logic
print("\nTracing through the function logic:")
print(f"1. header is not None: {header is not None}")

try:
    header_mtime = parse_http_date(header)
    print(f"2. Parsed header_mtime: {header_mtime}")
    
    print(f"3. Attempting int(mtime): int({mtime})")
    int_mtime = int(mtime)
    print(f"   Result: {int_mtime}")
    
    print(f"4. Comparing int(mtime) > header_mtime: {int_mtime} > {header_mtime}")
    if int_mtime > header_mtime:
        print("   Would raise ValueError (but doesn't in actual function)")
    else:
        print("   No ValueError raised, returns False")
        
except (ValueError, OverflowError) as e:
    print(f"   Exception caught: {type(e).__name__}: {e}")
    print("   Should return True")

# Test with positive overflow
print("\n" + "="*50)
print("Testing with positive overflow:")
mtime2 = 2**63  # Very large positive number
print(f"  mtime: {mtime2}")

result2 = was_modified_since(header, mtime2)
print(f"  Result: {result2}")

# Test edge cases around 32-bit boundaries
print("\n" + "="*50)
print("Testing edge cases around 32-bit boundaries:")
test_cases = [
    (-2**31 - 1, "Just below 32-bit signed min"),
    (-2**31, "32-bit signed min"),
    (2**31 - 1, "32-bit signed max"),
    (2**31, "Just above 32-bit signed max"),
]

for mtime_test, description in test_cases:
    result = was_modified_since(header, mtime_test)
    print(f"  mtime={mtime_test:15} ({description}): result={result}")