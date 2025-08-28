# Bug Report: pydantic.color Scientific Notation Parsing Failure

**Target**: `pydantic.color.parse_str`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `parse_str` function fails to parse color strings containing scientific notation, even though such strings can be legitimately generated when formatting floating-point color values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pydantic.color import parse_str

@given(
    st.floats(min_value=0, max_value=360, allow_nan=False),
    st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
)
def test_hsl_string_format_bug(h, s, l):
    hsl_str = f"hsl({h}, {s}%, {l}%)"
    result = parse_str(hsl_str)
    assert 0 <= result.r <= 1
    assert 0 <= result.g <= 1
    assert 0 <= result.b <= 1
```

**Failing input**: `h=0.0, s=0.0, l=5e-324`

## Reproducing the Bug

```python
from pydantic.color import parse_str

# Minimal failing examples
test_cases = [
    "hsl(0, 0%, 5e-324%)",           # HSL with tiny lightness
    "hsl(0, 1e-40%, 50%)",            # HSL with tiny saturation  
    "rgb(1e-40, 0, 0)",               # RGB with scientific notation
    "rgba(255, 255, 255, 1e-10)",    # RGBA with tiny alpha
]

for color_str in test_cases:
    try:
        result = parse_str(color_str)
        print(f"✓ {color_str}")
    except Exception as e:
        print(f"✗ {color_str} -> {e}")
```

## Why This Is A Bug

The `parse_str` function should handle all valid string representations of numeric color values. When Python formats very small or very large floating-point numbers, it automatically uses scientific notation (e.g., `1e-40`). The current regex patterns used for parsing RGB and HSL strings don't support scientific notation, causing valid color strings to be rejected.

This violates the expected contract that the parser should handle any string representation that Python might generate for valid numeric color values.

## Fix

The regex patterns for parsing numeric values in color strings need to be updated to support scientific notation. The patterns should be modified from:
- `\d{1,3}(?:\.\d+)?` (current pattern for RGB values)
- `\d{1,3}(?:\.\d+)?` (current pattern for HSL percentages)

To patterns that support scientific notation:
- `-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|-?\.\d+(?:[eE][+-]?\d+)?`

```diff
# In pydantic/color.py

- r_rgb = re.compile(
-     r'\s*rgba?\(\s*'
-     r'(\d{1,3}(?:\.\d+)?)\s*,\s*'
-     r'(\d{1,3}(?:\.\d+)?)\s*,\s*'
-     r'(\d{1,3}(?:\.\d+)?)'
-     ...
+ # Pattern that supports scientific notation
+ _float_pattern = r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|-?\.\d+(?:[eE][+-]?\d+)?'
+ r_rgb = re.compile(
+     r'\s*rgba?\(\s*'
+     f'({_float_pattern})\s*,\s*'
+     f'({_float_pattern})\s*,\s*'
+     f'({_float_pattern})'
+     ...

# Similar changes needed for r_hsl, r_rgb_v4_style, and r_hsl_v4_style patterns
```