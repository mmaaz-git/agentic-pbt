# Bug Report: pdfkit.pdfkit Boolean False Not Normalized to Empty String

**Target**: `pdfkit.pdfkit.PDFKit._normalize_options`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `_normalize_options` method incorrectly handles boolean False values. According to the code logic at line 247, boolean values should be converted to empty strings, but False is passed through unchanged due to incorrect conditional logic.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pdfkit.pdfkit import PDFKit
from pdfkit.configuration import Configuration

@given(
    option_name=st.text(min_size=1, max_size=30).filter(lambda x: not x.startswith('-')),
    option_value=st.booleans()
)
def test_boolean_normalization(option_name, option_value):
    class MockConfiguration(Configuration):
        def __init__(self):
            self.wkhtmltopdf = 'mock'
            self.meta_tag_prefix = 'pdfkit-'
            self.environ = {}
    
    pdf = PDFKit('test', 'string', configuration=MockConfiguration())
    options = {option_name: option_value}
    normalized = list(pdf._normalize_options(options))
    
    if normalized:
        key, value = normalized[0]
        assert value == '', f"Boolean {option_value} should normalize to empty string, got {repr(value)}"
```

**Failing input**: `option_name='0'`, `option_value=False`

## Reproducing the Bug

```python
from pdfkit.pdfkit import PDFKit
from pdfkit.configuration import Configuration

class MockConfiguration(Configuration):
    def __init__(self):
        self.wkhtmltopdf = 'mock'
        self.meta_tag_prefix = 'pdfkit-'
        self.environ = {}

pdf = PDFKit('test', 'string', configuration=MockConfiguration())
options = {'test-option': False}
normalized = list(pdf._normalize_options(options))
key, value = normalized[0]

print(f"Input: False")
print(f"Expected: '' (empty string)")
print(f"Actual: {repr(value)}")

assert value == '', f"Boolean False should be '', got {repr(value)}"
```

## Why This Is A Bug

The code at line 247 intends to convert boolean values to empty strings for command-line argument construction. The expression `'' if isinstance(value,bool) else value` is incorrect because when `value` is False, the condition evaluates to False due to Python's truthiness rules, causing False to be returned instead of an empty string. This breaks the intended normalization for wkhtmltopdf command-line options.

## Fix

```diff
--- a/pdfkit/pdfkit.py
+++ b/pdfkit/pdfkit.py
@@ -244,8 +244,8 @@ class PDFKit(object):
             for optval in value:
                 yield (normalized_key, optval)
         else:
-            normalized_value = '' if isinstance(value,bool) else value
-            yield (normalized_key, unicode(normalized_value) if value else value)
+            normalized_value = '' if isinstance(value, bool) else value
+            yield (normalized_key, unicode(normalized_value) if normalized_value else normalized_value)
```