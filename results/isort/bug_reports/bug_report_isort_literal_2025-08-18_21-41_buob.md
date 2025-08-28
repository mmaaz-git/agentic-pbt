# Bug Report: isort.literal Dict Not Sorted by Values

**Target**: `isort.literal._dict`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The _dict function claims to sort dictionaries by values but actually preserves key order due to PrettyPrinter behavior.

## Property-Based Test

```python
@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=2))
def test_dict_sorting_by_values(d):
    code = f"x = {repr(d)}"
    config = Config()
    
    result = assignment(code, "dict", ".py", config)
    
    _, literal_part = result.split(" = ", 1)
    result_dict = ast.literal_eval(literal_part.strip())
    
    items = list(result_dict.items())
    values = [v for k, v in items]
    
    # Values should be in sorted order
    assert values == sorted(values)
```

**Failing input**: `{'0': 0, '00': -1}`

## Reproducing the Bug

```python
import ast
from isort.literal import assignment
from isort.settings import Config

test_dict = {'a': 3, 'b': 1, 'c': 2}
code = f"x = {test_dict}"
config = Config()

result = assignment(code, "dict", ".py", config)

_, literal_part = result.split(" = ", 1)
result_dict = ast.literal_eval(literal_part.strip())

items = list(result_dict.items())
values = [v for k, v in items]

print(f"Values order: {values}")
assert values == sorted(values), f"Expected {sorted(values)}"
```

## Why This Is A Bug

The `_dict` function at line 89 attempts to sort dictionary items by value using `sorted(value.items(), key=lambda item: item[1])`. However, PrettyPrinter.pformat() internally re-sorts the dictionary by keys, undoing the value-based sorting. The function's implementation contradicts its apparent intent to sort by values.

## Fix

The issue is that PrettyPrinter's pformat method re-sorts dictionaries. To fix this, the function needs to format the sorted items manually:

```diff
@register_type("dict", dict)
def _dict(value: Dict[Any, Any], printer: ISortPrettyPrinter) -> str:
-    return printer.pformat(dict(sorted(value.items(), key=lambda item: item[1])))
+    sorted_items = sorted(value.items(), key=lambda item: item[1])
+    if not sorted_items:
+        return "{}"
+    formatted_items = [f"{printer.pformat(k)}: {printer.pformat(v)}" for k, v in sorted_items]
+    return "{" + ", ".join(formatted_items) + "}"
```