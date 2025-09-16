"""Minimal reproducer for the reset_caches inconsistency bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import htmldate.meta

# Replace an htmldate function with a mock that doesn't have cache_clear
original = htmldate.meta.compare_reference
htmldate.meta.compare_reference = lambda *args: 0

# This will crash with AttributeError
try:
    htmldate.meta.reset_caches()
    print("No error - unexpected!")
except AttributeError as e:
    print(f"AttributeError: {e}")

# Restore
htmldate.meta.compare_reference = original

# But charset_normalizer functions are handled gracefully
original_enc = htmldate.meta.encoding_languages if hasattr(htmldate.meta, 'encoding_languages') else None
htmldate.meta.encoding_languages = lambda *args: None

# This will NOT crash
try:
    htmldate.meta.reset_caches()
    print("No error for charset_normalizer - handled gracefully")
except AttributeError as e:
    print(f"Unexpected AttributeError: {e}")

# Restore
if original_enc:
    htmldate.meta.encoding_languages = original_enc