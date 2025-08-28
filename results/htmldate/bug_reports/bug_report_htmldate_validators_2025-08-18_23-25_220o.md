# Bug Report: htmldate.validators is_valid_format accepts invalid strftime codes

**Target**: `htmldate.validators.is_valid_format`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `is_valid_format` function incorrectly validates format strings containing invalid strftime codes, returning True when it should return False.

## Property-Based Test

```python
@given(st.sampled_from(["%q-%w-%e", "%Q", "%z%z%z"]))
def test_invalid_format_codes_rejected(format_string):
    # These contain invalid strftime codes like %q, %Q
    result = is_valid_format(format_string)
    assert result is False  # Should reject invalid codes
```

**Failing input**: `"%q-%w-%e"`

## Reproducing the Bug

```python
from htmldate.validators import is_valid_format
from datetime import datetime

invalid_format = "%q-%w-%e"
result = is_valid_format(invalid_format)

print(f"is_valid_format('{invalid_format}'): {result}")  # True (BUG!)

test_date = datetime(2020, 1, 1)
output = test_date.strftime(invalid_format)
print(f"strftime output: '{output}'")  # '%q-3- 1' (invalid codes passed through)

assert result is False  # AssertionError
```

## Why This Is A Bug

The function claims to "Validate the output format" but accepts format strings with invalid codes like %q and %Q. Python's strftime silently passes through invalid codes as literals, so just checking if strftime raises an exception is insufficient. The function should verify that only valid strftime format codes are used.

## Fix

The fix requires checking format codes against the set of valid strftime codes:

```diff
--- a/htmldate/validators.py
+++ b/htmldate/validators.py
@@ -75,11 +75,24 @@
 
 @lru_cache(maxsize=16)
 def is_valid_format(outputformat: str) -> bool:
     """Validate the output format in the settings"""
+    # Valid strftime codes
+    VALID_CODES = set('aAbBcdGHIjmMpSUVwWxXyYzZ%')
+    
     # test with date object
     dateobject = datetime(2017, 9, 1, 0, 0)
     try:
         dateobject.strftime(outputformat)
     except (TypeError, ValueError) as err:
         LOGGER.error("wrong output format or type: %s %s", outputformat, err)
         return False
+    
+    # Check for invalid format codes
+    import re
+    format_codes = re.findall(r'%(.)', outputformat)
+    for code in format_codes:
+        if code not in VALID_CODES:
+            LOGGER.error("invalid format code: %%%s in %s", code, outputformat)
+            return False
+    
     # test in abstracto (could be the only test)
     if not isinstance(outputformat, str) or "%" not in outputformat:
```