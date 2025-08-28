# Bug Report: pattern_filter Incorrect Handling of Empty Lists

**Target**: `pattern_filter` function from datadog_checks.utils.common
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `pattern_filter` function incorrectly treats empty whitelist/blacklist arrays the same as `None`, violating expected filter semantics where an empty whitelist should reject all items.

## Property-Based Test

```python
@given(st.lists(st.text()))
def test_pattern_filter_empty_patterns(items):
    """Test pattern_filter with empty whitelist/blacklist"""
    result_empty = pattern_filter(items, [], [])
    result_none = pattern_filter(items, None, None)
    
    assert result_empty == [], f"Empty whitelist should filter everything"
    assert result_none == items, f"None filters should pass everything"
```

**Failing input**: `items=['']`

## Reproducing the Bug

```python
import re

def pattern_filter(items, whitelist=None, blacklist=None, key=None):
    if key is None:
        key = lambda x: x
    
    if whitelist:
        items = [item for item in items if any(re.search(pattern, key(item)) for pattern in whitelist)]
    
    if blacklist:
        items = [item for item in items if not any(re.search(pattern, key(item)) for pattern in blacklist)]
    
    return items

items = ['a', 'b', 'c']

result_empty = pattern_filter(items, whitelist=[], blacklist=None)
print(f"With empty whitelist: {result_empty}")
print(f"Expected: [] (nothing can match empty pattern list)")

result_none = pattern_filter(items, whitelist=None, blacklist=None)
print(f"With None whitelist: {result_none}")
print(f"Expected: ['a', 'b', 'c'] (no filtering)")
```

## Why This Is A Bug

The function uses `if whitelist:` to check if filtering should be applied, but this evaluates to `False` for empty lists. This creates incorrect semantics where:
- An empty whitelist `[]` (which should reject everything) behaves like `None` (which accepts everything)
- An empty blacklist `[]` (which should reject nothing) behaves like `None` (which rejects nothing)

This violates the principle that an empty whitelist is the most restrictive filter possible.

## Fix

```diff
def pattern_filter(items, whitelist=None, blacklist=None, key=None):
    if key is None:
        key = lambda x: x
    
-   if whitelist:
+   if whitelist is not None:
+       if not whitelist:  # Empty whitelist filters everything
+           return []
        items = [item for item in items if any(re.search(pattern, key(item)) for pattern in whitelist)]
    
-   if blacklist:
+   if blacklist is not None:
+       if not blacklist:  # Empty blacklist filters nothing
+           pass  # Continue with current items
+       else:
            items = [item for item in items if not any(re.search(pattern, key(item)) for pattern in blacklist)]
    
    return items
```