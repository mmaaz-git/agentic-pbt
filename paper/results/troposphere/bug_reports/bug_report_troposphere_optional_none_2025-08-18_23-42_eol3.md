# Bug Report: troposphere Optional Properties Reject None Values

**Target**: `troposphere.BaseAWSObject`
**Severity**: Medium  
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Optional properties in troposphere AWS objects incorrectly reject None values during initialization, causing TypeError exceptions when None is explicitly passed for optional properties.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.amplify import App

@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.text(min_size=1, max_size=100),
    st.one_of(st.text(min_size=0, max_size=200), st.none()),
    st.one_of(st.text(min_size=0, max_size=100), st.none())
)
def test_app_optional_properties_accept_none(title, name, description, platform):
    """Optional properties should accept None values."""
    app = App(
        title,
        Name=name,
        Description=description,
        Platform=platform
    )
    assert app.properties['Name'] == name
    if description is not None:
        assert app.properties.get('Description') == description
    if platform is not None:
        assert app.properties.get('Platform') == platform
```

**Failing input**: `description=None` or `platform=None`

## Reproducing the Bug

```python
from troposphere.amplify import App, CustomRule

app = App('TestApp', Name='Test', Description=None)

rule = CustomRule(Source='src', Target='tgt', Status=None)
```

## Why This Is A Bug

Optional properties in troposphere objects should accept None values to indicate the property is not set. This is a common pattern in Python where None indicates absence of a value. The current behavior is inconsistent:

1. Not passing an optional property at all: Works fine
2. Passing None for an optional property: Raises TypeError

This inconsistency violates the principle of least surprise and makes the API harder to use, especially when constructing objects dynamically where None is a natural placeholder for optional values.

## Fix

The fix requires modifying the `__setattr__` method in BaseAWSObject to skip validation for None values on optional properties:

```diff
def __setattr__(self, name: str, value: Any) -> None:
    if (
        name in self.__dict__.keys()
        or "_BaseAWSObject__initialized" not in self.__dict__
    ):
        return dict.__setattr__(self, name, value)
    elif name in self.attributes:
        # ... existing code ...
    elif name in self.propnames:
+       # Skip None for optional properties
+       prop_required = self.props[name][1]
+       if value is None and not prop_required:
+           return  # Don't set None for optional properties
+       
        # Check the type of the object and compare against what we were
        # expecting.
        expected_type = self.props[name][0]
```