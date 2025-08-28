# Bug Report: pydantic.color RGBA 100% Alpha Value Parsing Failure

**Target**: `pydantic.color.parse_str`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `parse_str` function fails to parse RGBA color strings with alpha value of "100%", even though this is a valid percentage value representing full opacity.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pydantic.color import parse_str

@given(st.integers(min_value=0, max_value=100))
def test_rgba_percentage_alpha(pct):
    rgba_str = f"rgba(128, 128, 128, {pct}%)"
    result = parse_str(rgba_str)
    
    expected_alpha = pct / 100.0
    if expected_alpha == 1.0:
        assert result.alpha is None
    else:
        assert result.alpha is not None
        assert abs(result.alpha - expected_alpha) < 0.01
```

**Failing input**: `pct=100`

## Reproducing the Bug

```python
from pydantic.color import parse_str

# Test percentage alpha values
test_cases = [
    ('rgba(128, 128, 128, 0%)', True),     # Works
    ('rgba(128, 128, 128, 50%)', True),    # Works  
    ('rgba(128, 128, 128, 99%)', True),    # Works
    ('rgba(128, 128, 128, 100%)', False),  # FAILS - should work
]

for color_str, should_work in test_cases:
    try:
        result = parse_str(color_str)
        status = "✓" if should_work else "✗ (unexpected success)"
    except Exception:
        status = "✗ FAILED" if should_work else "✓ (expected failure)"
    print(f"{status} {color_str}")
```

## Why This Is A Bug

The RGBA format specification allows alpha values to be specified as percentages from 0% to 100%. The current regex pattern for RGBA uses `\d{1,2}%` to match percentage values, which only accepts 1 or 2 digits (0-99%) and incorrectly rejects the valid value "100%".

This violates the CSS Color Module specification and user expectations that 100% is a valid percentage value for full opacity.

## Fix

The regex pattern for matching percentage alpha values needs to be updated from `\d{1,2}%` to a pattern that accepts 0-100%.

```diff
# In pydantic/color.py

# Current regex pattern (simplified):
- r_rgb = re.compile(
-     r'...\s*,\s*(\d(?:\.\d+)?|\.\d+|\d{1,2}%))?\s*\)...'
-     #                                  ^^^^^^^^ only accepts 0-99%
- )

# Fixed pattern:
+ r_rgb = re.compile(
+     r'...\s*,\s*(\d(?:\.\d+)?|\.\d+|(?:100|[1-9]?\d)%))?\s*\)...'
+     #                                 ^^^^^^^^^^^^^^^^^ accepts 0-100%
+ )

# Similar fix needed for r_rgb_v4_style pattern
```

Alternative fix using `\d{1,3}%` would accept 0-999%, but the more precise pattern `(?:100|[1-9]?\d)%` ensures only valid percentages 0-100% are accepted.