# Bug Report: pdfkit TypeError on Non-String Input to from_string()

**Target**: `pdfkit.from_string()`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `pdfkit.from_string()` function crashes with a TypeError when passed non-string input (e.g., numbers, None, booleans) instead of gracefully handling or converting the input.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pdfkit
from pdfkit.pdfkit import PDFKit

class MockConfig:
    def __init__(self):
        self.wkhtmltopdf = '/usr/bin/wkhtmltopdf'
        self.meta_tag_prefix = 'pdfkit-'
        self.environ = {}

@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.none(),
    st.booleans()
))
def test_pdfkit_accepts_non_string_input(value):
    """Test that PDFKit handles non-string inputs gracefully"""
    pdf = PDFKit(value, 'string', configuration=MockConfig())
    # Should either work or raise a clear error, not TypeError from regex
    cmd = pdf.command()
```

**Failing input**: `42` (or any non-string value)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.pdfkit import PDFKit

class MockConfig:
    def __init__(self):
        self.wkhtmltopdf = '/usr/bin/wkhtmltopdf'
        self.meta_tag_prefix = 'pdfkit-'
        self.environ = {}

pdf = PDFKit(42, 'string', configuration=MockConfig())
cmd = pdf.command()
```

## Why This Is A Bug

The `from_string()` API function accepts an `input` parameter documented as "string with a desired text", but doesn't validate the type. When non-string values are passed, the code crashes with an obscure regex TypeError instead of either:
1. Converting the input to string automatically
2. Raising a clear ValueError with a helpful message

This violates the principle of least surprise - users might reasonably expect numeric content to be converted to string representation.

## Fix

```diff
--- a/pdfkit/pdfkit.py
+++ b/pdfkit/pdfkit.py
@@ -51,8 +51,11 @@ class PDFKit(object):
 
         self.options = OrderedDict()
         if self.source.isString():
-            self.options.update(self._find_options_in_meta(url_or_file))
-
+            # Ensure url_or_file is a string before regex operations
+            if isinstance(url_or_file, basestring):
+                self.options.update(self._find_options_in_meta(url_or_file))
+            else:
+                self.options.update(self._find_options_in_meta(str(url_or_file)))
         self.environ = self.configuration.environ
 
         if options is not None:
```