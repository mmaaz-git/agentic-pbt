# Bug Report: fire.decorators Type Inconsistency in SetParseFns

**Target**: `fire.decorators.SetParseFns`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `SetParseFns` decorator creates a tuple for positional arguments while `GetParseFns` default returns a list, causing type inconsistency in the API.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.decorators as decorators

@given(
    st.lists(st.sampled_from([str, int, float, bool]), min_size=0, max_size=3)
)
def test_set_parse_fns_type_consistency(positional_fns):
    def test_func():
        return None
    
    decorated = decorators.SetParseFns(*positional_fns)(test_func)
    parse_fns = decorators.GetParseFns(decorated)
    
    # This assertion fails - parse_fns['positional'] is a tuple, not a list
    assert parse_fns['positional'] == positional_fns
```

**Failing input**: `positional_fns=[]`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.decorators as decorators

def test_func():
    return None

# GetParseFns returns default with 'positional' as empty list
default_parse_fns = decorators.GetParseFns(test_func)
print(f"Default 'positional' type: {type(default_parse_fns['positional'])}")
print(f"Default 'positional' value: {default_parse_fns['positional']}")

# SetParseFns with empty args creates tuple
decorated = decorators.SetParseFns()(test_func)
result_parse_fns = decorators.GetParseFns(decorated)
print(f"After SetParseFns() 'positional' type: {type(result_parse_fns['positional'])}")
print(f"After SetParseFns() 'positional' value: {result_parse_fns['positional']}")

# Type inconsistency
assert default_parse_fns['positional'] == []  # passes
assert result_parse_fns['positional'] == ()   # passes
assert type(default_parse_fns['positional']) != type(result_parse_fns['positional'])  # passes - inconsistent!
```

## Why This Is A Bug

The `GetParseFns` function returns a default structure where 'positional' is an empty list (line 109 of decorators.py), but `SetParseFns` assigns the *args tuple directly to 'positional' (line 70), creating an inconsistency. Users cannot reliably predict whether 'positional' will be a list or tuple, making it harder to write code that processes these parse functions.

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