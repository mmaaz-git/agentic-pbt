# Bug Report: cryptography.utils.cached_property Incorrect Cache Attribute Naming

**Target**: `cryptography.utils.cached_property`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `cached_property` decorator creates cache attributes with unpredictable names containing the function object's memory address, making it impossible to programmatically access or clear the cache.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import cryptography.utils as utils

@given(st.text(min_size=1), st.integers())
def test_cached_property_predictable_cache_name(name, value):
    """Test that cached_property creates predictable cache attribute names"""
    # Filter for valid Python identifiers
    assume(name.isidentifier())
    assume(not name.startswith('_'))
    
    counter = [0]
    
    # Create a function with a specific name
    def prop_func(self):
        counter[0] += 1
        return value
    prop_func.__name__ = name
    
    # Create class with this cached property
    class TestClass:
        pass
    
    setattr(TestClass, name, utils.cached_property(prop_func))
    
    obj = TestClass()
    result = getattr(obj, name)
    
    # The cache should be stored under _cached_{property_name}
    expected_cache_name = f'_cached_{name}'
    assert hasattr(obj, expected_cache_name)  # FAILS
```

**Failing input**: `name='my_prop', value=42`

## Reproducing the Bug

```python
import cryptography.utils as utils

class Example:
    @utils.cached_property  
    def my_property(self):
        return 42

obj = Example()
value = obj.my_property

# Expected: cache stored as '_cached_my_property'
# Actual: cache stored as '_cached_<function Example.my_property at 0x...>'

cached_attrs = [attr for attr in dir(obj) if '_cached_' in attr]
print(f"Cache attribute: {cached_attrs[0]}")
# Output: _cached_<function Example.my_property at 0x7bc7134256c0>

# Cannot programmatically access the cache
expected_name = '_cached_my_property'
print(f"Has expected attribute: {hasattr(obj, expected_name)}")
# Output: False
```

## Why This Is A Bug

The cache attribute name includes the function object's string representation with memory address instead of using the function's `__name__` attribute. This makes the cache attribute:
1. Unpredictable and changes between runs
2. Impossible to access programmatically
3. Difficult to debug or inspect
4. Incompatible with serialization or introspection tools

## Fix

```diff
--- a/cryptography/utils.py
+++ b/cryptography/utils.py
@@ -115,7 +115,7 @@ def deprecated(
 
 
 def cached_property(func: Callable) -> property:
-    cached_name = f"_cached_{func}"
+    cached_name = f"_cached_{func.__name__}"
     sentinel = object()
 
     def inner(instance: object):
```