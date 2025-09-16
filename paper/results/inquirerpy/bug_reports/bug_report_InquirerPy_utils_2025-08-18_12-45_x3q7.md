# Bug Report: InquirerPy.utils.calculate_height Zero Height Not Clamped to 1

**Target**: `InquirerPy.utils.calculate_height`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `calculate_height` function fails to clamp height to 1 when the calculated height is exactly 0, violating the documented behavior that heights should be at least 1.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from unittest.mock import patch
from InquirerPy.utils import calculate_height
import math

@given(
    height_percent=st.integers(min_value=1, max_value=200),
    max_height_percent=st.integers(min_value=1, max_value=200),
    term_lines=st.integers(min_value=10, max_value=1000),
)
def test_calculate_height_clamping_to_minimum(height_percent, max_height_percent, term_lines):
    with patch("shutil.get_terminal_size") as mock_size:
        mock_size.return_value = (80, term_lines)
        
        result_height, result_max_height = calculate_height(
            f"{height_percent}%", f"{max_height_percent}%", height_offset=2
        )
        
        # Heights should never be less than 1 (as per lines 232-235 in utils.py)
        if result_height is not None:
            assert result_height >= 1, f"Height {result_height} should be >= 1"
        assert result_max_height >= 1, f"Max height {result_max_height} should be >= 1"
```

**Failing input**: `height_percent=1, max_height_percent=1, term_lines=200`

## Reproducing the Bug

```python
from unittest.mock import patch
from InquirerPy.utils import calculate_height

with patch("shutil.get_terminal_size") as mock_size:
    mock_size.return_value = (80, 200)
    
    result_height, result_max_height = calculate_height("1%", "1%", height_offset=2)
    
    print(f"Result height: {result_height}")  # Output: 0
    print(f"Result max_height: {result_max_height}")  # Output: 1
    
    assert result_height == 0  # Bug: should be 1
```

## Why This Is A Bug

The function documentation and code comments indicate that heights should be clamped to a minimum of 1 to ensure valid display dimensions. Lines 232-235 of utils.py attempt to enforce this:

```python
if dimmension_height and dimmension_height <= 0:
    dimmension_height = 1
```

However, when `dimmension_height` is exactly 0, the condition `dimmension_height and dimmension_height <= 0` evaluates to `False` because `0` is falsy in Python. This causes the height to remain 0 instead of being clamped to 1.

## Fix

```diff
--- a/InquirerPy/utils.py
+++ b/InquirerPy/utils.py
@@ -229,7 +229,7 @@ def calculate_height(
 
         if dimmension_height and dimmension_height > dimmension_max_height:
             dimmension_height = dimmension_max_height
-        if dimmension_height and dimmension_height <= 0:
+        if dimmension_height is not None and dimmension_height <= 0:
             dimmension_height = 1
         if dimmension_max_height <= 0:
             dimmension_max_height = 1
```