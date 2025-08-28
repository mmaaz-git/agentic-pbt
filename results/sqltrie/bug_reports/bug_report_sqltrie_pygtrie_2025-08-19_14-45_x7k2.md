# Bug Report: sqltrie.PyGTrie Inconsistent Error Handling for Non-Existent Prefixes

**Target**: `sqltrie.pygtrie.PyGTrie`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

PyGTrie.items() raises KeyError when called with a non-existent prefix, while PyGTrie.view() gracefully handles the same situation by returning an empty trie. This inconsistency makes the API unpredictable.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqltrie.pygtrie import PyGTrie

@st.composite
def trie_keys(draw):
    length = draw(st.integers(min_value=0, max_value=5))
    return tuple(draw(st.text(min_size=1, max_size=10)) for _ in range(length))

@st.composite  
def trie_with_items(draw):
    trie = PyGTrie()
    n_items = draw(st.integers(min_value=0, max_value=10))
    items = {}
    for _ in range(n_items):
        key = draw(trie_keys())
        value = draw(st.binary(min_size=1, max_size=100))
        trie[key] = value
        items[key] = value
    return trie, items

@given(trie_with_items(), trie_keys())
def test_items_with_prefix(trie_items, prefix):
    trie, _ = trie_items
    
    for key, value in trie.items(prefix=prefix):
        assert key[:len(prefix)] == prefix
```

**Failing input**: `trie_items=(<empty trie>, {}), prefix=('0',)`

## Reproducing the Bug

```python
from sqltrie.pygtrie import PyGTrie

trie = PyGTrie()
# Empty trie or trie without the requested prefix

# This raises KeyError
try:
    list(trie.items(prefix=('nonexistent',)))
except KeyError as e:
    print(f"items() raises KeyError: {e}")

# But view() handles it gracefully
view = trie.view(('nonexistent',))
print(f"view() returns empty trie: {list(view.items())}")
```

## Why This Is A Bug

The inconsistency between `items()` and `view()` is problematic:

1. Both methods deal with prefixes that may not exist in the trie
2. `view()` has defensive code (lines 93-97) that catches KeyError and returns an empty result
3. `items()` directly passes through to the underlying pygtrie without error handling
4. Users would expect consistent behavior - either both should raise KeyError or both should handle gracefully

This violates the principle of least surprise and makes the API harder to use correctly.

## Fix

```diff
--- a/sqltrie/pygtrie.py
+++ b/sqltrie/pygtrie.py
@@ -61,7 +61,11 @@ class PyGTrie(AbstractTrie):
     def items(self, prefix=None, shallow=False):
         kwargs = {"shallow": shallow}
         if prefix is not None:
             kwargs["prefix"] = prefix
 
-        yield from self._trie.iteritems(**kwargs)
+        try:
+            yield from self._trie.iteritems(**kwargs)
+        except KeyError:
+            # Handle non-existent prefix gracefully, like view() does
+            return
```