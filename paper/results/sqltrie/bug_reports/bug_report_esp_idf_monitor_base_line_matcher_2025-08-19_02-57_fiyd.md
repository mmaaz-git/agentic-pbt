# Bug Report: esp_idf_monitor.base.line_matcher Filter Parsing Fails with Colons in Tags

**Target**: `esp_idf_monitor.base.line_matcher.LineMatcher`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

LineMatcher's filter string parsing fails when tags contain colons, causing ValueError exceptions when creating filters with tags like ":" or "tag:subtag".

## Property-Based Test

```python
from hypothesis import given, strategies as st
from esp_idf_monitor.base.line_matcher import LineMatcher

@given(
    st.text(min_size=1, max_size=20),  # tag
    st.sampled_from(['N', 'E', 'W', 'I', 'D', 'V', '*', ''])  # level
)
def test_line_matcher_filter_construction(tag, level):
    """Property: Any valid tag and level should create a valid filter string"""
    if level:
        filter_str = f"{tag}:{level}"
    else:
        filter_str = tag
    
    matcher = LineMatcher(filter_str)
    assert isinstance(matcher._dict, dict)
```

**Failing input**: `tag=':'`, `level='N'` (creates filter string `"::N"`)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')
from esp_idf_monitor.base.line_matcher import LineMatcher

tag = ':'
level = 'V'
filter_str = f"{tag}:{level}"  # Creates "::V"

matcher = LineMatcher(filter_str)  # Raises ValueError: Missing ":" in filter ::V
```

## Why This Is A Bug

The LineMatcher class is designed to parse filter strings in the format "tag:level". However, the parsing logic splits the string by ':' and expects exactly 1 or 2 parts. When a tag itself contains ':', this creates ambiguity that the parser cannot handle. This violates the expected behavior that any tag string should be usable in a filter.

## Fix

The issue is in the filter parsing logic at line 36-48 of line_matcher.py. The code needs to handle the last colon as the separator between tag and level, not the first one.

```diff
--- a/esp_idf_monitor/base/line_matcher.py
+++ b/esp_idf_monitor/base/line_matcher.py
@@ -33,17 +33,18 @@ class LineMatcher(object):
         if len(items) == 0:
             self._dict['*'] = self.LEVEL_V  # default is to print everything
         for f in items:
-            s = f.split(r':')
-            if len(s) == 1:
+            # Use rsplit with maxsplit=1 to handle tags containing ':'
+            s = f.rsplit(':', 1)
+            if len(s) == 1:  # No colon found
                 # specifying no warning level defaults to verbose level
                 lev = self.LEVEL_V
-            elif len(s) == 2:
+                tag = s[0]
+            else:  # len(s) == 2
+                tag = s[0]
                 if len(s[0]) == 0:
                     raise ValueError('No tag specified in filter ' + f)
                 try:
                     lev = self.level[s[1].upper()]
                 except KeyError:
                     raise ValueError('Unknown warning level in filter ' + f)
-            else:
-                raise ValueError('Missing ":" in filter ' + f)
-            self._dict[s[0]] = lev
+            self._dict[tag] = lev
```