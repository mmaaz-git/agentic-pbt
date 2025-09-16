# Bug Report: htmldate.meta Inconsistent Error Handling in reset_caches()

**Target**: `htmldate.meta.reset_caches`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `reset_caches()` function has inconsistent error handling between htmldate functions and charset_normalizer functions, causing it to crash when htmldate functions are mocked without `cache_clear` attribute.

## Property-Based Test

```python
@settings(max_examples=500)
@given(st.data())
def test_cache_clear_attribute_missing(data):
    """Test behavior when cache_clear attribute is missing from functions."""
    
    function_names = data.draw(st.sets(
        st.sampled_from([
            'compare_reference',
            'filter_ymd_candidate',
            'is_valid_date', 
            'is_valid_format',
            'try_date_expr'
        ]),
        min_size=1,
        max_size=5
    ))
    
    # Replace functions with mocks lacking cache_clear
    for func_name in function_names:
        if func_name == 'compare_reference':
            htmldate.meta.compare_reference = lambda *args: 0
    
    # This raises AttributeError for htmldate functions
    # but would be handled gracefully for charset_normalizer functions
    with pytest.raises(AttributeError):
        htmldate.meta.reset_caches()
```

**Failing input**: When any htmldate function is replaced with a mock lacking `cache_clear`

## Reproducing the Bug

```python
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
```

## Why This Is A Bug

The function has inconsistent error handling:
- Lines 34-40 protect charset_normalizer functions with try/except blocks
- Lines 28-32 don't protect htmldate's own functions
This violates the principle of consistent error handling and makes the function fragile when used with mocked/replaced functions during testing.

## Fix

```diff
--- a/htmldate/meta.py
+++ b/htmldate/meta.py
@@ -24,11 +24,16 @@
 def reset_caches() -> None:
     """Reset all known LRU caches used to speed-up processing.
     This may release some memory."""
     # htmldate
-    compare_reference.cache_clear()
-    filter_ymd_candidate.cache_clear()
-    is_valid_date.cache_clear()
-    is_valid_format.cache_clear()
-    try_date_expr.cache_clear()
+    try:
+        compare_reference.cache_clear()
+        filter_ymd_candidate.cache_clear()
+        is_valid_date.cache_clear()
+        is_valid_format.cache_clear()
+        try_date_expr.cache_clear()
+    # prevent issues with mocked/replaced functions
+    except (AttributeError, NameError) as err:
+        LOGGER.error("impossible to clear cache for function: %s", err)
+    
     # charset_normalizer
     try:
         encoding_languages.cache_clear()
```