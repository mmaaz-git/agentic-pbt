"""Test that demonstrates inconsistency in reset_caches error handling."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import htmldate.meta
from unittest.mock import MagicMock

print("Testing inconsistency in error handling between htmldate and charset_normalizer functions...")
print("=" * 80)

# Test 1: charset_normalizer function missing cache_clear
print("\nTest 1: charset_normalizer function without cache_clear")
print("-" * 40)

# Save originals
original_encoding = getattr(htmldate.meta, 'encoding_languages', None)

# Replace with mock that doesn't have cache_clear
mock_encoding = MagicMock(spec=[])  # No cache_clear attribute
htmldate.meta.encoding_languages = mock_encoding

try:
    htmldate.meta.reset_caches()
    print("SUCCESS: reset_caches() handled missing cache_clear gracefully for charset_normalizer")
except AttributeError as e:
    print(f"FAILURE: reset_caches() raised AttributeError for charset_normalizer: {e}")

# Restore
if original_encoding:
    htmldate.meta.encoding_languages = original_encoding

# Test 2: htmldate function missing cache_clear  
print("\nTest 2: htmldate function without cache_clear")
print("-" * 40)

# Save original
original_compare = htmldate.meta.compare_reference

# Replace with function that doesn't have cache_clear
def mock_compare(*args, **kwargs):
    return 0

htmldate.meta.compare_reference = mock_compare

try:
    htmldate.meta.reset_caches()
    print("SUCCESS: reset_caches() handled missing cache_clear gracefully for htmldate function")
except AttributeError as e:
    print(f"FAILURE: reset_caches() raised AttributeError for htmldate function: {e}")

# Restore
htmldate.meta.compare_reference = original_compare

print("\n" + "=" * 80)
print("INCONSISTENCY FOUND:")
print("- charset_normalizer functions are protected with try/except (lines 34-40)")
print("- htmldate functions are NOT protected (lines 28-32)")
print("This means reset_caches() will crash if htmldate functions are replaced/mocked")
print("without cache_clear, but handles charset_normalizer functions gracefully.")
print("\nThis is a design inconsistency that could be considered a bug.")