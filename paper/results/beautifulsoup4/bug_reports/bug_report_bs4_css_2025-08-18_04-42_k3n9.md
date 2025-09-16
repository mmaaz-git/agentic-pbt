# Bug Report: bs4.css Namespace Handling with Precompiled Selectors

**Target**: `bs4.css.CSS`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The CSS class in BeautifulSoup4 raises a ValueError when using precompiled selectors with the namespaces parameter, affecting all selector methods (select, select_one, iselect, closest, match, filter).

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from bs4 import BeautifulSoup

@given(st.booleans())
@settings(max_examples=50)
def test_namespace_normalization(is_compiled):
    """Test the _ns method for namespace normalization."""
    soup = BeautifulSoup("<html><body><div>test</div></body></html>", 'html.parser')
    soup._namespaces = {'test': 'http://test.com'}
    css = soup.css
    
    if is_compiled:
        selector = css.compile('div')
        custom_ns = {'custom': 'http://custom.com'}
        results = css.select(selector, namespaces=custom_ns)  # Raises ValueError
        assert isinstance(results, ResultSet)
```

**Failing input**: `is_compiled=True`

## Reproducing the Bug

```python
from bs4 import BeautifulSoup

html = """<html>
<body>
    <div id="test">Test content</div>
</body>
</html>"""

soup = BeautifulSoup(html, 'html.parser')
css = soup.css

# Compile a selector
compiled_selector = css.compile('div')

# This raises ValueError
custom_namespaces = {'custom': 'http://example.com'}
results = css.select(compiled_selector, namespaces=custom_namespaces)
```

## Why This Is A Bug

The CSS._ns() method's comment states that precompiled selectors "already have a namespace context compiled in, which cannot be replaced", but the implementation doesn't handle this case correctly. When a precompiled selector is used with a namespaces parameter, soupsieve raises a ValueError that propagates to the user. The CSS class should either ignore the namespaces parameter for precompiled selectors or provide a clearer error message.

## Fix

```diff
--- a/bs4/css.py
+++ b/bs4/css.py
@@ -80,11 +80,13 @@ class CSS(object):
     def _ns(
         self, ns: Optional[_NamespaceMapping], select: str
     ) -> Optional[_NamespaceMapping]:
         """Normalize a dictionary of namespaces."""
-        if not isinstance(select, self.api.SoupSieve) and ns is None:
+        if isinstance(select, self.api.SoupSieve):
             # If the selector is a precompiled pattern, it already has
             # a namespace context compiled in, which cannot be
             # replaced.
+            return None
+        if ns is None:
             ns = self.tag._namespaces
         return ns
```