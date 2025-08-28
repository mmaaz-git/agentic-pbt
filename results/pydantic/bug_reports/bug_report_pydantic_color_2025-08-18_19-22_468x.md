# Bug Report: pydantic.color HSL Round-Trip Precision Loss

**Target**: `pydantic.color.Color`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Color class loses precision when converting to HSL string format and back, causing RGB values to differ by up to 4 units due to insufficient decimal precision in the as_hsl() method.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pydantic.color import Color

@given(st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
))
def test_hsl_conversion_preserves_color(rgb_tuple):
    color1 = Color(rgb_tuple)
    hsl_str = color1.as_hsl()
    color2 = Color(hsl_str)
    
    rgb1 = color1.as_rgb_tuple(alpha=False)
    rgb2 = color2.as_rgb_tuple(alpha=False)
    
    for v1, v2 in zip(rgb1, rgb2):
        assert abs(v1 - v2) <= 1  # Fails - differences can be up to 4
```

**Failing input**: `(40, 238, 65)`

## Reproducing the Bug

```python
from pydantic.color import Color

rgb_input = (40, 238, 65)
color1 = Color(rgb_input)
hsl_str = color1.as_hsl()
print(f"HSL string: {hsl_str}")

color2 = Color(hsl_str)
rgb_output = color2.as_rgb_tuple(alpha=False)

print(f"Input:  RGB{rgb_input}")
print(f"Output: RGB{rgb_output}")
print(f"Differences: {[abs(a - b) for a, b in zip(rgb_input, rgb_output)]}")
print(f"Max difference: {max(abs(a - b) for a, b in zip(rgb_input, rgb_output))}")
```

## Why This Is A Bug

The `as_hsl()` method formats HSL values with insufficient precision:
- Hue: formatted with 0 decimal places (`{h * 360:0.0f}`)
- Saturation/Lightness: formatted as whole percentages (`{s:0.0%}`)

This precision loss violates the expected round-trip property where converting a color to HSL string and back should preserve the RGB values within a reasonable tolerance (typically ±1 for rounding). The actual differences can be up to 4, which may be visible in color-critical applications.

## Fix

```diff
--- a/pydantic/color.py
+++ b/pydantic/color.py
@@ -193,11 +193,11 @@ class Color(_repr.Representation):
     def as_hsl(self) -> str:
         """Color as an `hsl(<h>, <s>, <l>)` or `hsl(<h>, <s>, <l>, <a>)` string."""
         if self._rgba.alpha is None:
             h, s, li = self.as_hsl_tuple(alpha=False)  # type: ignore
-            return f'hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%})'
+            return f'hsl({h * 360:0.2f}, {s:0.2%}, {li:0.2%})'
         else:
             h, s, li, a = self.as_hsl_tuple(alpha=True)  # type: ignore
-            return f'hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%}, {round(a, 2)})'
+            return f'hsl({h * 360:0.2f}, {s:0.2%}, {li:0.2%}, {round(a, 2)})'
```