# Bug Report: troposphere.robomaker Rejects None for Optional Fields

**Target**: `troposphere.robomaker`  
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Optional fields in troposphere.robomaker classes reject explicit None values despite being marked as optional, violating Python conventions.

## Property-Based Test

```python
@given(st.data())
def test_from_dict_preserves_all_fields(data):
    """Test that from_dict preserves all valid fields for various classes"""
    robot_suite = robomaker.RobotSoftwareSuite(
        Name=data.draw(aws_name_strategy),
        Version=data.draw(st.one_of(st.none(), version_strategy))
    )
    
    app_kwargs = {'RobotSoftwareSuite': robot_suite}
    
    if data.draw(st.booleans()):
        app_kwargs['Name'] = data.draw(aws_name_strategy)
    if data.draw(st.booleans()):
        app_kwargs['CurrentRevisionId'] = data.draw(aws_name_strategy)
    
    original = robomaker.RobotApplication(**app_kwargs)
    dict_repr = original.to_dict()
    reconstructed = robomaker.RobotApplication.from_dict('TestApp', dict_repr)
    assert dict_repr == reconstructed.to_dict()
```

**Failing input**: `Name='0', Version=None`

## Reproducing the Bug

```python
import troposphere.robomaker as robomaker

suite = robomaker.RobotSoftwareSuite(Name='ROS', Version=None)
```

## Why This Is A Bug

Optional parameters in Python conventionally accept None to indicate absence of a value. The field 'Version' is marked as optional (False) in props, and omitting it entirely works fine:

```python
suite1 = robomaker.RobotSoftwareSuite(Name='ROS')  # Works
suite2 = robomaker.RobotSoftwareSuite(Name='ROS', Version=None)  # Fails
```

This violates the principle of least surprise and breaks common patterns like:
- Conditional assignment: `Version=version if version else None`
- Dict unpacking with None defaults: `**{'Name': 'ROS', 'Version': None}`
- Programmatic construction where None indicates "use default"

## Fix

Optional fields should filter out None values before type checking:

```diff
def __setattr__(self, name, value):
    if name in self.props:
        expected_type, required = self.props[name]
+       if value is None and not required:
+           return  # Don't set optional fields with None value
        if not isinstance(value, expected_type):
            self._raise_type(name, value, expected_type)
    super().__setattr__(name, value)
```