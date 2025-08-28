# Bug Report: praw.util.snake.snake_case_keys Data Loss from Key Collisions

**Target**: `praw.util.snake.snake_case_keys`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `snake_case_keys` function silently loses data when converting dictionaries with keys that differ only in case, as both keys get transformed to the same snake_case key.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from praw.util import snake
import string

identifier_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=50
).filter(lambda s: s[0].isalpha() or s[0] == '_')

@given(st.dictionaries(
    keys=identifier_strategy,
    values=st.one_of(
        st.integers(),
        st.text(),
        st.booleans(),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ),
    min_size=0,
    max_size=50
))
def test_snake_case_keys_value_preservation(dictionary):
    """Test that snake_case_keys preserves all values unchanged."""
    result = snake.snake_case_keys(dictionary)
    
    original_values = set(str(v) for v in dictionary.values())
    result_values = set(str(v) for v in result.values())
    
    assert original_values == result_values, f"Values changed: {original_values} != {result_values}"
```

**Failing input**: `{'A': 0, 'a': 1}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')
from praw.util import snake

dictionary = {'A': 0, 'a': 1}
result = snake.snake_case_keys(dictionary)

print(f"Input:  {dictionary}")
print(f"Output: {result}")
print(f"Data lost: value {dictionary['A']} is missing")

api_response = {
    'Id': 123,
    'ID': 456,
    'userName': 'john',
    'UserName': 'jane'
}
converted = snake.snake_case_keys(api_response)
print(f"\nRealistic scenario:")
print(f"Input:  {api_response}")
print(f"Output: {converted}")
print(f"Lost 'Id': 123 and 'userName': 'john'")
```

## Why This Is A Bug

This violates the fundamental expectation that transforming dictionary keys should not lose data. When working with case-sensitive systems (like many APIs, databases, or file systems), having keys that differ only in case is valid. The function silently discards values without warning, which can lead to data corruption and hard-to-debug issues in production systems.

## Fix

```diff
--- a/praw/util/snake.py
+++ b/praw/util/snake.py
@@ -15,7 +15,18 @@ def camel_to_snake(name: str) -> str:
 
 def snake_case_keys(dictionary: dict[str, Any]) -> dict[str, Any]:
     """Return a new dictionary with keys converted to snake_case.
 
     :param dictionary: The dict to be corrected.
+    :raises ValueError: If converting keys would cause a collision.
 
     """
-    return {camel_to_snake(k): v for k, v in dictionary.items()}
+    result = {}
+    for k, v in dictionary.items():
+        new_key = camel_to_snake(k)
+        if new_key in result:
+            raise ValueError(
+                f"Key collision: both '{k}' and another key convert to '{new_key}'. "
+                f"This would cause data loss."
+            )
+        result[new_key] = v
+    return result
```