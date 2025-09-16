#!/usr/bin/env python3
"""Minimal reproduction of cache key collision bug in django.templatetags.cache"""

import django
from django.conf import settings

# Minimal Django configuration
settings.configure(DEBUG=True)
django.setup()

from django.templatetags.cache import make_template_fragment_key

# Demonstration of the bug
fragment_name = "user_profile"

# These two DIFFERENT vary_on lists produce the SAME cache key
vary_on_1 = ["user:123"]       # Single string containing colon
vary_on_2 = ["user", "123"]    # Two separate strings

key_1 = make_template_fragment_key(fragment_name, vary_on_1)
key_2 = make_template_fragment_key(fragment_name, vary_on_2)

print(f"Input 1: make_template_fragment_key('{fragment_name}', {vary_on_1})")
print(f"Result:  {key_1}")
print()
print(f"Input 2: make_template_fragment_key('{fragment_name}', {vary_on_2})")  
print(f"Result:  {key_2}")
print()
print(f"Cache keys are identical: {key_1 == key_2}")

if key_1 == key_2:
    print("\nBUG CONFIRMED: Different vary_on inputs produce identical cache keys!")
    print("This could lead to incorrect cache retrieval in production.")