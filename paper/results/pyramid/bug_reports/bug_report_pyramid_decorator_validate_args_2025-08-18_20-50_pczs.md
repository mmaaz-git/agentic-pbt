# Bug Report: pyramid_decorator validate_arguments Fails with **kwargs Functions

**Target**: `pyramid_decorator.validate_arguments`
**Severity**: High  
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `validate_arguments` decorator fails to validate any arguments when applied to functions that use `**kwargs`, allowing invalid values to pass through without validation.

## Property-Based Test

```python
@given(
    st.dictionaries(
        st.sampled_from(['a', 'b', 'c']),
        st.integers(min_value=0, max_value=100),
        min_size=1,
        max_size=3
    )
)
def test_validate_arguments_all_validators_called(arg_values):
    """Property: All validators should be called for their respective arguments."""
    
    called_validators = []
    
    def make_validator(name):
        def validator(value):
            called_validators.append(name)
            return value < 50
        return validator
    
    validators = {name: make_validator(name) for name in arg_values.keys()}
    
    @pyramid_decorator.validate_arguments(**validators)
    def func(**kwargs):
        return sum(kwargs.values())
    
    will_fail = any(v >= 50 for v in arg_values.values())
    called_validators.clear()
    
    if will_fail:
        try:
            func(**arg_values)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
    else:
        result = func(**arg_values)
        assert result == sum(arg_values.values())
    
    assert set(called_validators) == set(arg_values.keys())
```

**Failing input**: `arg_values={'a': 50}`

## Reproducing the Bug

```python
import pyramid_decorator

def validate_positive(value):
    return value > 0

@pyramid_decorator.validate_arguments(x=validate_positive)
def func(**kwargs):
    return kwargs.get('x', 0)

result = func(x=-10)
print(f"Result: {result}")
```

## Why This Is A Bug

When a function uses `**kwargs` to capture keyword arguments, the `inspect.signature().bind()` method puts all keyword arguments into a single 'kwargs' dictionary parameter. The validation logic at line 253 checks `if arg_name in bound.arguments`, but for `**kwargs` functions, individual argument names like 'x' are not in `bound.arguments` - only 'kwargs' is present. This causes all validators to be skipped, allowing invalid values to pass through unchecked.

## Fix

```diff
--- a/pyramid_decorator.py
+++ b/pyramid_decorator.py
@@ -250,9 +250,16 @@ def validate_arguments(**validators: Dict[str, Callable]) -> Callable[[F], F]:
             
             # Validate each argument that has a validator
             for arg_name, validator in validators.items():
-                if arg_name in bound.arguments:
+                # Check if argument is in bound arguments directly
+                if arg_name in bound.arguments:  
                     value = bound.arguments[arg_name]
                     if not validator(value):
                         raise ValueError(f"Invalid value for {arg_name}: {value}")
+                # Also check in **kwargs if present
+                elif 'kwargs' in bound.arguments and arg_name in bound.arguments['kwargs']:
+                    value = bound.arguments['kwargs'][arg_name]
+                    if not validator(value):
+                        raise ValueError(f"Invalid value for {arg_name}: {value}")
                         
             return func(*args, **kwargs)
```