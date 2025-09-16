# Bug Report: pyramid.static _add_vary Function Preserves Existing Duplicates

**Target**: `pyramid.static._add_vary`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_add_vary` function in pyramid.static is designed to prevent duplicate Vary headers (case-insensitive), but it fails to clean up pre-existing duplicates in the response.vary list.

## Property-Based Test

```python
@given(
    st.lists(st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122))),
    st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122))
)
def test_add_vary_no_duplicates(existing_vary, new_option):
    """_add_vary should not add duplicate Vary headers (case-insensitive)."""
    response = Mock()
    response.vary = existing_vary.copy() if existing_vary else []
    
    _add_vary(response, new_option)
    
    # Check that no duplicates exist (case-insensitive)
    vary_lower = [v.lower() for v in response.vary]
    assert len(vary_lower) == len(set(vary_lower)), \
        f"Duplicate vary headers found: {response.vary}"
```

**Failing input**: `existing_vary=['A', 'A'], new_option='A'`

## Reproducing the Bug

```python
from pyramid.static import _add_vary
from unittest.mock import Mock

response = Mock()
response.vary = ['Accept-Encoding', 'Accept-Encoding']

_add_vary(response, 'Accept-Encoding')

assert response.vary == ['Accept-Encoding', 'Accept-Encoding']
print(f"Bug: response.vary contains duplicates: {response.vary}")
```

## Why This Is A Bug

The function checks whether to add a new header by comparing against existing headers (line 258), but it doesn't remove any pre-existing duplicates. A function designed to prevent duplicates should ensure the list contains no duplicates after it runs, not just avoid adding new ones.

## Fix

```diff
def _add_vary(response, option):
    vary = response.vary or []
+   # Remove existing duplicates first
+   seen = set()
+   unique_vary = []
+   for v in vary:
+       if v.lower() not in seen:
+           seen.add(v.lower())
+           unique_vary.append(v)
+   vary = unique_vary
    if not any(x.lower() == option.lower() for x in vary):
        vary.append(option)
    response.vary = vary
```