# Bug Report: mdxpy DescFlag Enum Parsing Fails for Underscored Names Without Underscores

**Target**: `mdxpy.mdx.DescFlag._missing_`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The DescFlag enum's `_missing_` method fails to parse valid enum names when underscores are removed, even though it's designed to be flexible with case and spacing.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from mdxpy.mdx import DescFlag

@given(st.sampled_from(["self", "after", "before", "SELF", "AFTER", "BEFORE", 
                        "self_and_after", "SELF_AND_AFTER", "selfandafter",
                        "before_and_after", "BEFORE_AND_AFTER", "beforeandafter"]))
def test_desc_flag_parsing(flag_str):
    """DescFlag should parse string values correctly (case-insensitive, space-insensitive)"""
    parsed = DescFlag._missing_(flag_str)
    assert parsed is not None
    assert isinstance(parsed, DescFlag)
```

**Failing input**: `'selfandafter'`

## Reproducing the Bug

```python
from mdxpy.mdx import DescFlag

# These work correctly
DescFlag._missing_("SELF_AND_AFTER")  # OK
DescFlag._missing_("self_and_after")  # OK

# This fails but should work
try:
    DescFlag._missing_("selfandafter")
except ValueError as e:
    print(f"Error: {e}")
```

## Why This Is A Bug

The `_missing_` method is designed to provide flexible parsing of enum values, handling different cases and removing spaces. However, it doesn't handle the case where a user provides the enum name without underscores. Since the method already removes spaces (`.replace(" ", "")`), it's reasonable to expect it would also handle underscores being omitted, especially since "SELF_AND_AFTER" is a valid enum member name.

## Fix

```diff
--- a/mdxpy/mdx.py
+++ b/mdxpy/mdx.py
@@ -25,7 +25,7 @@ class DescFlag(Enum):
         if value is None:
             return None
         for member in cls:
-            if member.name.lower() == value.replace(" ", "").lower():
+            if member.name.lower().replace("_", "") == value.replace(" ", "").replace("_", "").lower():
                 return member
         # default
         raise ValueError(f"Invalid Desc Flag type: '{value}'")