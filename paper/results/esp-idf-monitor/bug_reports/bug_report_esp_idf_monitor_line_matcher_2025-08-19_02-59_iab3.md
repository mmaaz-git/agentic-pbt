# Bug Report: esp_idf_monitor LineMatcher fails to match tags with leading/trailing spaces

**Target**: `esp_idf_monitor.base.line_matcher.LineMatcher`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

LineMatcher incorrectly handles filter tags containing leading or trailing spaces. The filter parsing strips whitespace from tags during initialization, but the regex preserves spaces when extracting tags from log lines, causing legitimate matches to fail.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from esp_idf_monitor.base.line_matcher import LineMatcher

@given(
    tag=st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=20),
    spaces=st.sampled_from([' ', '  ', '   ']),
    level=st.sampled_from(['E', 'W', 'I', 'D', 'V'])
)
def test_line_matcher_with_spaces(tag, spaces, level):
    # Add spaces to tag
    tag_with_spaces = spaces + tag
    filter_str = f"{tag_with_spaces}:{level}"
    matcher = LineMatcher(filter_str)
    
    # Create properly formatted ESP-IDF log line
    test_line = f"{level} (12345) {tag_with_spaces}: Test message"
    
    # Should match since tag and level match the filter
    assert matcher.match(test_line), f"Failed to match tag with spaces: '{tag_with_spaces}'"
```

**Failing input**: Tag with any leading/trailing spaces, e.g., `tag=' wifi'`, `level='E'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')
from esp_idf_monitor.base.line_matcher import LineMatcher

# Create filter with tag containing leading space
filter_str = " wifi:E"
matcher = LineMatcher(filter_str)

# This log line should match but doesn't
log_line = "E (1234)  wifi: Connection error"
result = matcher.match(log_line)

print(f"Filter: '{filter_str}'")
print(f"Log line: '{log_line}'")
print(f"Match result: {result}")  # False
print(f"Expected: True")
```

## Why This Is A Bug

The LineMatcher's filter parsing uses `split()` which strips whitespace, storing "wifi" in the filter dictionary. However, during matching, the regex correctly extracts " wifi" (with space) from the log line. The lookup for " wifi" in a dictionary containing only "wifi" fails, incorrectly rejecting valid log lines.

This violates the expected behavior that a filter should match log lines with the same tag, regardless of surrounding whitespace handling inconsistencies.

## Fix

```diff
--- a/esp_idf_monitor/base/line_matcher.py
+++ b/esp_idf_monitor/base/line_matcher.py
@@ -54,7 +54,10 @@ class LineMatcher(object):
             m = self._re.search(line)
             if m:
                 lev = self.level[m.group(1)]
-                if m.group(2) in self._dict:
+                # Strip spaces from extracted tag to match filter parsing behavior
+                extracted_tag = m.group(2).strip()
+                if extracted_tag in self._dict:
-                    return self._dict[m.group(2)] >= lev
+                    return self._dict[extracted_tag] >= lev
                 return self._dict.get('*', self.LEVEL_N) >= lev
         except (KeyError, IndexError):
```

Alternatively, preserve spaces in both filter parsing and matching for consistency.