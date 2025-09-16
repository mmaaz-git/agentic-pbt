# Bug Report: pdfkit.pdfkit Meta Tag Content Parsing Truncation

**Target**: `pdfkit.pdfkit.PDFKit._find_options_in_meta`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The meta tag content parsing regex truncates values containing quote or apostrophe characters, causing incorrect option extraction from HTML meta tags.

## Property-Based Test

```python
@given(
    st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20),
    st.text(min_size=1, max_size=100).filter(lambda x: '"' not in x and "'" not in x),
    st.sampled_from(['pdfkit-', 'custom-', 'test-'])
)
def test_meta_tag_parsing(option_name, option_value, prefix):
    config = MockConfiguration(meta_tag_prefix=prefix)
    pdf = PDFKit('test', 'string', configuration=config)
    
    html = f'<html><head><meta name="{prefix}{option_name}" content="{option_value}"></head><body></body></html>'
    found_options = pdf._find_options_in_meta(html)
    
    assert option_name in found_options
    assert found_options[option_name] == option_value
```

**Failing input**: `option_name='a', option_value='>0', prefix='pdfkit-'`

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

pdf = PDFKit('test', 'string', configuration=MockConfig())
html = '<html><head><meta name="pdfkit-a" content=">0"></head><body></body></html>'
options = pdf._find_options_in_meta(html)
print(f'Expected ">0", got "{options.get("a")}"')
```

## Why This Is A Bug

The regex pattern `content=["\']([^"\']*)'` in line 302 of pdfkit.py is malformed - it starts with `["\']` but doesn't end with a closing quote/apostrophe pattern. This causes the regex to match only up to the first character that looks like it could be a closing delimiter, truncating content values like ">0" to just ">".

## Fix

```diff
--- a/pdfkit/pdfkit.py
+++ b/pdfkit/pdfkit.py
@@ -299,7 +299,7 @@ class PDFKit(object):
             if re.search('name=["\']%s' % self.configuration.meta_tag_prefix, x):
                 name = re.findall('name=["\']%s([^"\']*)' %
                                   self.configuration.meta_tag_prefix, x)[0]
-                found[name] = re.findall('content=["\']([^"\']*)', x)[0]
+                found[name] = re.findall('content=["\']([^"\']*)["\']', x)[0]
 
         return found
```