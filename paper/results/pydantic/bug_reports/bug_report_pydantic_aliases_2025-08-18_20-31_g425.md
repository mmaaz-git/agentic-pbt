# Bug Report: pydantic.aliases.AliasGenerator Inconsistent Non-Callable Handling

**Target**: `pydantic.aliases.AliasGenerator`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

AliasGenerator accepts non-callable values for its transformation functions but handles them inconsistently, either silently returning None or raising TypeError depending on the combination of parameters.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pydantic.aliases

@given(st.data())
def test_alias_generator_callable_validation(data):
    """Test that AliasGenerator properly validates callable arguments"""
    
    non_callable = data.draw(st.one_of(
        st.integers(),
        st.text(),
        st.lists(st.integers())
    ))
    
    if not callable(non_callable):
        gen = pydantic.aliases.AliasGenerator(
            alias=non_callable,
            validation_alias=non_callable,
            serialization_alias=non_callable
        )
        
        # This returns (None, None, None) instead of validating
        result = gen.generate_aliases("test")
        assert result == (None, None, None)  # Unexpected silent failure
```

**Failing input**: `non_callable=0` (or any non-callable value)

## Reproducing the Bug

```python
import pydantic.aliases

# Case 1: All non-callable - silently returns None
gen1 = pydantic.aliases.AliasGenerator(
    alias=42,
    validation_alias=42, 
    serialization_alias=42
)
result1 = gen1.generate_aliases('test_field')
print(f"All non-callable: {result1}")  # (None, None, None)

# Case 2: Mixed None and non-callable - raises TypeError
gen2 = pydantic.aliases.AliasGenerator(
    alias=None,
    validation_alias=42
)
try:
    result2 = gen2.generate_aliases('test_field')
except TypeError as e:
    print(f"Mixed: TypeError - {e}")  # 'int' object is not callable

# Case 3: What the docstring says should happen
# "alias: A callable that takes a field name and returns an alias"
# Non-callables should be rejected at construction or usage
```

## Why This Is A Bug

1. **Inconsistent behavior**: The same invalid input (non-callable) produces different results depending on other parameters
2. **Violates documented contract**: The docstring explicitly states parameters should be "A callable that takes a field name"
3. **Silent failure**: When all parameters are non-callable, it silently returns None instead of raising an error
4. **Confusing for users**: The inconsistent behavior makes debugging difficult

## Fix

The fix should validate that parameters are either None or callable at construction time:

```diff
 class AliasGenerator:
     def __init__(
         self,
         alias: Callable[[str], str] | None = None,
         validation_alias: Callable[[str], str | AliasPath | AliasChoices] | None = None,
         serialization_alias: Callable[[str], str] | None = None,
     ) -> None:
+        if alias is not None and not callable(alias):
+            raise TypeError(f"alias must be callable or None, got {type(alias).__name__}")
+        if validation_alias is not None and not callable(validation_alias):
+            raise TypeError(f"validation_alias must be callable or None, got {type(validation_alias).__name__}")
+        if serialization_alias is not None and not callable(serialization_alias):
+            raise TypeError(f"serialization_alias must be callable or None, got {type(serialization_alias).__name__}")
         self.alias = alias
         self.validation_alias = validation_alias
         self.serialization_alias = serialization_alias
```