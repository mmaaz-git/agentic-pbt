"""Investigate the bug found in reset_caches."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import htmldate.meta
from htmldate.core import compare_reference

# Check if compare_reference has cache_clear
print(f"compare_reference has cache_clear: {hasattr(compare_reference, 'cache_clear')}")

# Save the original
original_clear = compare_reference.cache_clear

# Remove cache_clear
del compare_reference.cache_clear

print(f"After deletion, has cache_clear: {hasattr(compare_reference, 'cache_clear')}")

# Try reset_caches - this should raise AttributeError but doesn't
try:
    htmldate.meta.reset_caches()
    print("ERROR: reset_caches() did not raise AttributeError when compare_reference.cache_clear was missing!")
except AttributeError as e:
    print(f"Good: AttributeError raised as expected: {e}")
except Exception as e:
    print(f"Unexpected exception: {type(e).__name__}: {e}")

# Restore
compare_reference.cache_clear = original_clear

# Let me look at the source code to understand why
print("\n--- Checking reset_caches implementation ---")
import inspect
print(inspect.getsource(htmldate.meta.reset_caches))