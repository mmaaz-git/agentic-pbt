# Bug Report: pdfkit.pdfkit Boolean False Handling in Options

**Target**: `pdfkit.pdfkit.PDFKit._normalize_options`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The _normalize_options method incorrectly yields boolean False values instead of converting them to empty strings, violating the method's documented behavior for boolean option values.

## Property-Based Test

```python
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.one_of(
        st.text(min_size=0),
        st.booleans(),
        st.none(),
        st.lists(st.text(), min_size=2, max_size=2)
    )
))
def test_genargs_handles_values(options):
    pdf = PDFKit('test', 'string', options=options, configuration=MockConfiguration())
    args = list(pdf._genargs(options))
    
    for arg in args:
        assert arg is None or arg == '' or isinstance(arg, str)
```

**Failing input**: `options={'0': False}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')
from pdfkit.pdfkit import PDFKit
import os

class MockConfig:
    def __init__(self):
        self.wkhtmltopdf = '/fake/path'
        self.meta_tag_prefix = 'pdfkit-'
        self.environ = os.environ

pdf = PDFKit('test', 'string', options={'quiet': False}, configuration=MockConfig())
args = list(pdf._genargs({'quiet': False}))
print(f'Args: {args}')
print(f'Type of second arg: {type(args[1])}')
```

## Why This Is A Bug

In _normalize_options (line 247-248), when value is a boolean False:
- Line 247 correctly sets `normalized_value = ''` for booleans
- Line 248 incorrectly evaluates `if value` which is False, causing it to yield the original False value instead of the normalized empty string

This breaks the contract that _genargs should only yield strings or None, causing downstream code to receive unexpected boolean values.

## Fix

```diff
--- a/pdfkit/pdfkit.py
+++ b/pdfkit/pdfkit.py
@@ -245,7 +245,7 @@ class PDFKit(object):
                     yield (normalized_key, optval)
             else:
                 normalized_value = '' if isinstance(value,bool) else value
-                yield (normalized_key, unicode(normalized_value) if value else value)
+                yield (normalized_key, unicode(normalized_value) if normalized_value else normalized_value)
 
     def _normalize_arg(self, arg):
         return arg.lower()
```