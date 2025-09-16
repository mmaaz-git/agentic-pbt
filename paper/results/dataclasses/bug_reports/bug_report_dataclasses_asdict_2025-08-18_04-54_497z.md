# Bug Report: dataclasses.asdict() Does Not Convert Sets/Frozensets to JSON-Serializable Types

**Target**: `dataclasses.asdict`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `asdict()` function preserves `set` and `frozenset` types instead of converting them to lists, making the resulting dictionary non-JSON-serializable, which breaks the common use case of serializing dataclass instances to JSON.

## Property-Based Test

```python
from dataclasses import dataclass, asdict
from hypothesis import given, strategies as st
import json
import pytest


@given(st.sets(st.one_of(st.integers(), st.text(max_size=10)), min_size=1, max_size=10))
def test_asdict_with_sets_not_json_serializable(items):
    @dataclass
    class TestClass:
        data: set
    
    instance = TestClass(data=items)
    result = asdict(instance)
    
    assert isinstance(result['data'], set)
    
    with pytest.raises(TypeError, match="Object of type set is not JSON serializable"):
        json.dumps(result)
```

**Failing input**: `{0}` (or any non-empty set)

## Reproducing the Bug

```python
from dataclasses import dataclass, asdict
import json

@dataclass
class DataWithCollections:
    list_field: list
    tuple_field: tuple
    set_field: set
    frozenset_field: frozenset

instance = DataWithCollections(
    list_field=[1, 2, 3],
    tuple_field=(4, 5, 6),
    set_field={7, 8, 9},
    frozenset_field=frozenset({10, 11})
)

result = asdict(instance)

print(f"list type: {type(result['list_field'])}")
print(f"tuple type: {type(result['tuple_field'])}")
print(f"set type: {type(result['set_field'])}")
print(f"frozenset type: {type(result['frozenset_field'])}")

try:
    json.dumps(result)
    print("JSON serialization: Success")
except TypeError as e:
    print(f"JSON serialization failed: {e}")
```

## Why This Is A Bug

The `asdict()` function's documentation states it recursively converts dataclass instances to dictionaries and "will also look into built-in containers: tuples, lists, and dicts." While the documentation doesn't explicitly promise JSON serializability, the function converts tuples to tuples (which are JSON-serializable), but fails to handle sets and frozensets, falling back to `copy.deepcopy()` which preserves their non-JSON-serializable types.

This is inconsistent behavior that breaks the common pattern of using `asdict()` for JSON serialization, which is mentioned in the source code comments as "The main use case here is json.dumps" (line 1402-1403 of dataclasses.py).

## Fix

The fix would be to add explicit handling for `set` and `frozenset` types in the `_asdict_inner` function, converting them to lists similar to how tuples are preserved but remain JSON-serializable:

```diff
--- a/dataclasses.py
+++ b/dataclasses.py
@@ -1386,6 +1386,10 @@ def _asdict_inner(obj, dict_factory):
         }
     elif obj_type is tuple:
         return tuple([_asdict_inner(v, dict_factory) for v in obj])
+    elif obj_type is set:
+        return [_asdict_inner(v, dict_factory) for v in obj]
+    elif obj_type is frozenset:
+        return [_asdict_inner(v, dict_factory) for v in obj]
     elif issubclass(obj_type, tuple):
         if hasattr(obj, '_fields'):
             # obj is a namedtuple.  Recurse into it, but the returned
```

Alternatively, to preserve type information while ensuring JSON compatibility, sets could be converted to sorted lists for consistent ordering.