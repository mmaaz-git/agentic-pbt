# Bug Report: pdfkit.pdfkit Regex Injection in Meta Tag Parsing

**Target**: `pdfkit.pdfkit.PDFKit._find_options_in_meta`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `_find_options_in_meta` method in pdfkit fails to escape regex special characters in the meta_tag_prefix, causing regex compilation errors when the prefix contains characters like parentheses, brackets, or other regex metacharacters.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pdfkit
from pdfkit.pdfkit import PDFKit
from pdfkit.configuration import Configuration

@given(
    prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='<>"\'')),
    option_name=st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_characters='<>"\'')),
    option_value=st.text(min_size=0, max_size=50, alphabet=st.characters(blacklist_characters='<>"\''))
)
def test_meta_tag_extraction(prefix, option_name, option_value):
    html = f'<html><head><meta name="{prefix}{option_name}" content="{option_value}"></head><body></body></html>'
    config = Configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf', meta_tag_prefix=prefix)
    pdf = PDFKit(html, 'string', configuration=config)
    found_options = pdf._find_options_in_meta(html)
    assert option_name in found_options
    assert found_options[option_name] == option_value
```

**Failing input**: `prefix='('`, `option_name='0'`, `option_value=''`

## Reproducing the Bug

```python
import re
from pdfkit.pdfkit import PDFKit
from pdfkit.configuration import Configuration

class MockConfiguration(Configuration):
    def __init__(self, wkhtmltopdf='mock', meta_tag_prefix='pdfkit-', environ=None):
        self.wkhtmltopdf = wkhtmltopdf
        self.meta_tag_prefix = meta_tag_prefix
        self.environ = environ or {}

malicious_prefix = "pdfkit("
html = f'<html><head><meta name="{malicious_prefix}option" content="value"></head></html>'
config = MockConfiguration(meta_tag_prefix=malicious_prefix)

try:
    pdf = PDFKit(html, 'string', configuration=config)
except re.error as e:
    print(f"Regex compilation error: {e}")
```

## Why This Is A Bug

The code constructs a regex pattern using user-controlled input without escaping special regex characters. When the meta_tag_prefix contains regex metacharacters, the regex compilation fails, preventing the library from functioning correctly. This violates the expected behavior that any string should be valid as a meta_tag_prefix.

## Fix

```diff
--- a/pdfkit/pdfkit.py
+++ b/pdfkit/pdfkit.py
@@ -296,10 +296,10 @@ class PDFKit(object):
         found = {}
 
         for x in re.findall('<meta [^>]*>', content):
-            if re.search('name=["\']%s' % self.configuration.meta_tag_prefix, x):
+            if re.search('name=["\']%s' % re.escape(self.configuration.meta_tag_prefix), x):
                 name = re.findall('name=["\']%s([^"\']*)' %
-                                  self.configuration.meta_tag_prefix, x)[0]
+                                  re.escape(self.configuration.meta_tag_prefix), x)[0]
                 found[name] = re.findall('content=["\']([^"\']*)', x)[0]
 
         return found
```