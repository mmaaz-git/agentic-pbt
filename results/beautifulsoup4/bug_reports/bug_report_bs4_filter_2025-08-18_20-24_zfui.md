# Bug Report: bs4.filter.SoupStrainer Case-Sensitive Attribute Matching

**Target**: `bs4.filter.SoupStrainer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

SoupStrainer performs case-sensitive attribute name matching while HTML parsers convert all attribute names to lowercase, causing strainers with uppercase attribute names to never match parsed HTML tags.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
from bs4 import BeautifulSoup
from bs4.filter import SoupStrainer

@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1, max_size=10),
    st.text(max_size=50)
)
def test_soupstrainer_attribute_case_sensitivity(attr_name_upper, attr_value):
    assume(attr_name_upper.isalpha())
    
    strainer = SoupStrainer(attrs={attr_name_upper: attr_value})
    html = f'<div {attr_name_upper}="{attr_value}"></div>'
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('div')
    
    assert attr_name_upper.lower() in tag.attrs
    assert tag.attrs[attr_name_upper.lower()] == attr_value
    
    result = strainer.matches_tag(tag)
    assert result == True  # Expected behavior (currently fails)
```

**Failing input**: `attr_name_upper='CLASS', attr_value='highlight'`

## Reproducing the Bug

```python
from bs4 import BeautifulSoup
from bs4.filter import SoupStrainer

strainer = SoupStrainer(attrs={'CLASS': 'highlight'})
html = '<div CLASS="highlight">Important text</div>'
soup = BeautifulSoup(html, 'html.parser')

div_tag = soup.find('div')
print(f"Tag attributes: {div_tag.attrs}")  # {'class': ['highlight']}

matches = strainer.matches_tag(div_tag)
print(f"Strainer matches: {matches}")  # False (should be True)

results = soup.find_all(strainer)
print(f"find_all results: {results}")  # [] (should find the div)
```

## Why This Is A Bug

HTML attributes are case-insensitive per the HTML specification. Users reasonably expect that a SoupStrainer created with `attrs={'CLASS': 'value'}` should match tags with `class="value"` after parsing. The current behavior violates this expectation and makes SoupStrainer unusable with uppercase attribute names.

## Fix

```diff
--- a/bs4/filter.py
+++ b/bs4/filter.py
@@ -482,7 +482,7 @@ class SoupStrainer(ElementFilter):
             }
             
         if attrs:
-            self.attribute_rules = defaultdict(list)
+            self.attribute_rules = defaultdict(list)
             for key, value in attrs.items():
                 possible_value = _NormalizableAttribute._normalize(value)
                 if possible_value is None:
@@ -491,7 +491,7 @@ class SoupStrainer(ElementFilter):
                 normalized = self._ensure_rules(
                     possible_value, AttributeValueMatchRule
                 )
-                self.attribute_rules[key] = normalized
+                self.attribute_rules[key.lower()] = normalized
         else:
             self.attribute_rules = defaultdict(list)
```

Alternatively, modify the lookup in `matches_tag`:

```diff
--- a/bs4/filter.py
+++ b/bs4/filter.py
@@ -644,8 +644,13 @@ class SoupStrainer(ElementFilter):
         # If there are attribute rules for a given attribute, at least
         # one of them must match. If there are rules for multiple
         # attributes, each attribute must have at least one match.
         for attr, rules in self.attribute_rules.items():
-            attr_value = tag.get(attr, None)
+            # Try exact case first, then lowercase for case-insensitive matching
+            attr_value = tag.get(attr, None)
+            if attr_value is None and attr.lower() != attr:
+                # HTML parsers convert attributes to lowercase
+                attr_value = tag.get(attr.lower(), None)
             this_attr_match = self._attribute_match(attr_value, rules)
             if not this_attr_match:
                 return False
```