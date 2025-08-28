# Bug Report: mdxpy DescFlag Enum Cannot Parse Underscore-Containing Members Without Underscores

**Target**: `mdxpy.mdx.DescFlag`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The DescFlag enum's `_missing_` method fails to parse enum member names that contain underscores when the input has underscores removed, even though it claims to handle case-insensitive and space-insensitive parsing.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from mdxpy.mdx import DescFlag

@given(st.sampled_from(["beforeandafter", "BEFOREANDAFTER", "selfandafter", "SELFANDAFTER",
                        "selfandbefore", "SELFANDBEFORE", "selfbeforeafter", "SELFBEFOREAFTER"]))
def test_desc_flag_enum_underscore_handling(flag_str):
    """DescFlag enum should parse strings without underscores for members with underscores"""
    parsed = DescFlag(flag_str)
    assert parsed is not None
```

**Failing input**: `'beforeandafter'`

## Reproducing the Bug

```python
from mdxpy.mdx import DescFlag

# This should work given the intent of case/space insensitive parsing
try:
    result = DescFlag("beforeandafter")
    print(f"Success: {result}")
except ValueError as e:
    print(f"Failed: {e}")
    
# But only the version with underscores works
result2 = DescFlag("before_and_after")
print(f"With underscores works: {result2.name}")
```

## Why This Is A Bug

The DescFlag enum has members like `BEFORE_AND_AFTER`, `SELF_AND_AFTER`, etc. that contain underscores. The `_missing_` method attempts to provide flexible parsing by removing spaces and doing case-insensitive comparison, but it doesn't account for underscores in the enum member names. Users might reasonably expect "beforeandafter" to match the `BEFORE_AND_AFTER` member, similar to how spaces are handled, but this fails.

## Fix

```diff
@classmethod
def _missing_(cls, value: str):
    if value is None:
        return None
+    normalized_value = value.replace(" ", "").replace("_", "").lower()
    for member in cls:
-        if member.name.lower() == value.replace(" ", "").lower():
+        if member.name.replace("_", "").lower() == normalized_value:
            return member
    # default
    raise ValueError(f"Invalid Desc Flag type: '{value}'")
```