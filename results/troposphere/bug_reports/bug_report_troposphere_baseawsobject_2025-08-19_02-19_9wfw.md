# Bug Report: troposphere BaseAWSObject Type Hint Mismatch

**Target**: `troposphere.BaseAWSObject.__init__`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `title` parameter in `BaseAWSObject.__init__` has type hint `Optional[str]` but lacks a default value, making it a required positional argument despite the type hint suggesting it's optional.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.pinpoint as pinpoint

@given(
    name=st.text(min_size=1, max_size=50),
    tags=st.dictionaries(st.text(), st.text())
)
def test_app_initialization(name, tags):
    """Test that App can be initialized according to its type hints"""
    # Type hint suggests this should work since title is Optional[str]
    app = pinpoint.App(Name=name, Tags=tags)
    assert app.properties.get("Name") == name
```

**Failing input**: Any valid input triggers the error immediately

## Reproducing the Bug

```python
from troposphere.pinpoint import App

# Type hint says Optional[str], suggesting this should work
app = App(Name="TestApp")
# TypeError: BaseAWSObject.__init__() missing 1 required positional argument: 'title'
```

## Why This Is A Bug

The type annotation `Optional[str]` in `BaseAWSObject.__init__` indicates that `None` is an acceptable value and suggests the parameter is optional. However, the parameter has no default value, making it a required positional argument. This creates a contract violation where:

1. Static type checkers will accept code that omits the `title` parameter
2. The runtime will fail with a TypeError for the same code
3. Users following IDE autocomplete based on type hints will encounter unexpected errors

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -160,7 +160,7 @@ class BaseAWSObject:
     def __init__(
         self,
-        title: Optional[str],
+        title: Optional[str] = None,
         template: Optional[Template] = None,
         validation: bool = True,
         **kwargs: Any,
```

This fix adds a default value of `None` to match the `Optional[str]` type hint, making the parameter truly optional as the type system indicates.