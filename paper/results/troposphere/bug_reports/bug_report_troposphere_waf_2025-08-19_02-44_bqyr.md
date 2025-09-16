# Bug Report: troposphere.waf no_validation() Method Doesn't Disable Validation

**Target**: `troposphere.waf.Action` and related classes
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `no_validation()` method in troposphere AWS resource classes sets `do_validation = False` but validation still occurs during attribute assignment, making the method ineffective.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.waf as waf

@given(st.text().filter(lambda x: x not in ["ALLOW", "BLOCK", "COUNT"]))
def test_no_validation_disables_validation(invalid_type):
    """Test that no_validation() actually disables validation as documented"""
    # Create with valid type
    action = waf.Action(Type="ALLOW")
    
    # Disable validation
    action.no_validation()
    
    # Should be able to set invalid type now
    action.Type = invalid_type  # This fails despite no_validation()
    
    # Should be able to serialize with validation=False
    result = action.to_dict(validation=False)
    assert result["Type"] == invalid_type
```

**Failing input**: Any string not in `["ALLOW", "BLOCK", "COUNT"]`, e.g., `"INVALID"`

## Reproducing the Bug

```python
import troposphere.waf as waf

action = waf.Action(Type="ALLOW")
print(f"do_validation before: {action.do_validation}")  # True

action.no_validation()
print(f"do_validation after: {action.do_validation}")   # False

try:
    action.Type = "INVALID"
    print("Successfully set invalid type")
except ValueError as e:
    print(f"Failed: {e}")  # This happens despite no_validation()
```

## Why This Is A Bug

The `no_validation()` method exists to allow users to bypass validation when needed (e.g., for custom extensions or testing). It sets `do_validation = False`, but the `__setattr__` method performs validation regardless of this flag, making the method useless. This violates the API contract implied by the method's existence and name.

## Fix

The validation in `__setattr__` should check the `do_validation` flag before performing validation:

```diff
# In troposphere/__init__.py, class BaseAWSObject.__setattr__
def __setattr__(self, name, value):
    # ... existing code ...
    if name in self.props:
        expected_type = self.props[name][0]
        if isinstance(expected_type, list):
            # ... existing list handling ...
        elif isinstance(expected_type, type):
            # ... existing type checking ...
        elif callable(expected_type):
-           value = expected_type(value)
+           if getattr(self, 'do_validation', True):
+               value = expected_type(value)
    # ... rest of method ...
```