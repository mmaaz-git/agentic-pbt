# Bug Report: pyramid.i18n Missing _catalog Attribute in Domain Translations

**Target**: `pyramid.i18n.Translations`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`Translations` objects created without a fileobj lack the `_catalog` attribute, causing AttributeError when used as domain-specific translations via `dgettext()`, `dugettext()`, `dngettext()`, and `dungettext()` methods.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.i18n import Translations

@given(
    domain=st.text(min_size=1, max_size=30).filter(lambda x: not x.isspace()),
    singular=st.text(min_size=1, max_size=50),
    plural=st.text(min_size=1, max_size=50),
    n=st.integers(min_value=0, max_value=1000)
)
def test_translations_dngettext_handles_domains(domain, singular, plural, n):
    trans = Translations()
    domain_trans = Translations(domain=domain)
    trans.add(domain_trans)
    
    result = trans.dngettext(domain, singular, plural, n)
    assert isinstance(result, str)
```

**Failing input**: `domain='0', singular='0', plural='0', n=0`

## Reproducing the Bug

```python
from pyramid.i18n import Translations

trans = Translations()
domain_trans = Translations(domain='testdomain')
trans.add(domain_trans)

result = trans.dngettext('testdomain', 'singular', 'plural', 1)
```

## Why This Is A Bug

The `Translations` class inherits from `gettext.GNUTranslations`, which only initializes `_catalog` when a file object is provided. When created without a fileobj, `_catalog` is never initialized. The `dngettext()` method retrieves the domain-specific translation and calls `ngettext()` on it, which attempts to access `_catalog`, resulting in an AttributeError.

Notably, `make_localizer()` works around this by manually setting `translations._catalog = {}` after creation, indicating awareness of this issue. However, users creating `Translations` objects directly face this crash.

## Fix

```diff
--- a/pyramid/i18n.py
+++ b/pyramid/i18n.py
@@ -244,6 +244,9 @@ class Translations(gettext.GNUTranslations):
         self.plural = DEFAULT_PLURAL
         gettext.GNUTranslations.__init__(self, fp=fileobj)
         self.files = list(filter(None, [getattr(fileobj, 'name', None)]))
+        # Initialize _catalog if not created by GNUTranslations.__init__
+        if not hasattr(self, '_catalog'):
+            self._catalog = {}
         self.domain = domain
         self._domains = {}
```