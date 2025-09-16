# Bug Report: packaging.utils is_normalized_name Incorrectly Accepts Consecutive Dashes

**Target**: `packaging.utils.is_normalized_name`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `is_normalized_name` function incorrectly accepts package names containing consecutive dashes (e.g., "a--b", "0--0") when it should reject them according to normalized name conventions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import packaging.utils

@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=5),
    st.integers(min_value=2, max_value=5),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=5)
)
def test_is_normalized_name_rejects_double_dash(prefix, dash_count, suffix):
    """is_normalized_name should reject names with consecutive dashes"""
    name = f"{prefix}{'-' * dash_count}{suffix}"
    assert not packaging.utils.is_normalized_name(name)
```

**Failing input**: `prefix='0', dash_count=2, suffix='0'` (resulting in name='0--0')

## Reproducing the Bug

```python
import packaging.utils

# These should all return False but incorrectly return True
print(packaging.utils.is_normalized_name('0--0'))    # True (BUG: should be False)
print(packaging.utils.is_normalized_name('a--b'))    # True (BUG: should be False)
print(packaging.utils.is_normalized_name('1--2'))    # True (BUG: should be False)

# Correctly rejects triple dashes and longer names with double dashes
print(packaging.utils.is_normalized_name('a---b'))     # False (correct)
print(packaging.utils.is_normalized_name('foo--bar'))  # False (correct)
```

## Why This Is A Bug

The function uses regex pattern `^([a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])$` with a negative lookahead `(?!--)` that's meant to prevent consecutive dashes. However, the lookahead only checks if a character is not followed by two dashes, not if it's part of a consecutive dash sequence. 

For input '0--0':
- First dash matches because it's followed by '-0' (not '--')  
- Second dash matches because it's followed by '0' (not '--')

This violates the normalized name format which should not allow consecutive dashes, similar to how `canonicalize_name` collapses multiple separators into a single dash.

## Fix

The regex pattern needs to be corrected to properly reject consecutive dashes. A potential fix would be to modify the pattern to not allow a dash to be preceded or followed by another dash:

```diff
- _normalized_regex = re.compile(r"^([a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])$")
+ _normalized_regex = re.compile(r"^([a-z0-9]|[a-z0-9]([a-z0-9]|(?<!-)-(?!-))*[a-z0-9])$")
```

This uses both negative lookbehind `(?<!-)` and lookahead `(?!-)` to ensure dashes are isolated.