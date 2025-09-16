# Bug Report: fire.decorators SetParseFns Type Inconsistency

**Target**: `fire.decorators.SetParseFns`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

SetParseFns converts list inputs to tuples, breaking the round-trip property where retrieved values should match the input type.

## Property-Based Test

```python
@given(
    simple_functions(),
    st.lists(parse_functions(), min_size=0, max_size=3),
    st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=st.characters(categories=['Ll'])),
        parse_functions(),
        min_size=0,
        max_size=3
    )
)
def test_set_parse_fns_round_trip(func, positional_fns, named_fns):
    """SetParseFns values should be retrievable via GetParseFns."""
    decorated = decorators.SetParseFns(*positional_fns, **named_fns)(func)
    retrieved = decorators.GetParseFns(decorated)
    assert retrieved['positional'] == positional_fns
    assert retrieved['named'] == named_fns
```

**Failing input**: `func=<any function>, positional_fns=[], named_fns={}`

## Reproducing the Bug

```python
from fire import decorators

def test_func():
    return 42

positional_fns = []
decorated = decorators.SetParseFns(*positional_fns)(test_func)
retrieved = decorators.GetParseFns(decorated)

print(f"Input: {positional_fns} (type: {type(positional_fns)})")
print(f"Retrieved: {retrieved['positional']} (type: {type(retrieved['positional'])})")
assert retrieved['positional'] == positional_fns  # Fails: () != []
```

## Why This Is A Bug

SetParseFns uses `*positional` in its signature, which converts any iterable input to a tuple. This breaks the expectation that the same type passed in should be retrievable, violating the round-trip property. Users passing lists expect to get lists back, not tuples.

## Fix

```diff
--- a/fire/decorators.py
+++ b/fire/decorators.py
@@ -67,7 +67,7 @@ def SetParseFns(*positional, **named):
   """
   def _Decorator(fn):
     parse_fns = GetParseFns(fn)
-    parse_fns['positional'] = positional
+    parse_fns['positional'] = list(positional)
     parse_fns['named'].update(named)
     _SetMetadata(fn, FIRE_PARSE_FNS, parse_fns)
     return fn
```