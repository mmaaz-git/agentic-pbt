# Bug Report: troposphere.applicationsignals Optional Properties Reject None Values

**Target**: `troposphere.applicationsignals` (affects entire troposphere library)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Optional properties in troposphere AWS resource classes incorrectly reject `None` values, causing TypeErrors when users explicitly pass `None` for optional properties.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.applicationsignals import ExclusionWindow, Window

@given(
    duration=st.integers(min_value=1, max_value=365),
    duration_unit=st.sampled_from(["DAY", "MONTH"]),
    reason=st.text(max_size=100)
)
def test_optional_property_none_handling(duration, duration_unit, reason):
    window = Window(Duration=duration, DurationUnit=duration_unit)
    
    # Should handle empty string by converting to None
    if reason == '':
        excl_window = ExclusionWindow(Window=window, Reason=None)
    else:
        excl_window = ExclusionWindow(Window=window, Reason=reason)
    
    assert excl_window.to_dict() is not None
```

**Failing input**: `reason=''` (which gets converted to `None` in the test)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.applicationsignals import ExclusionWindow, Window, ServiceLevelObjective, Goal

# Bug 1: String properties reject None
window = Window(Duration=1, DurationUnit='DAY')
excl = ExclusionWindow(Window=window, Reason=None)
# TypeError: <class 'troposphere.applicationsignals.ExclusionWindow'>: None.Reason is <class 'NoneType'>, expected <class 'str'>

# Bug 2: Validator properties reject None  
goal = Goal(AttainmentGoal=None)
# ValueError: None is not a valid double

# Bug 3: Any optional property fails with None
slo = ServiceLevelObjective('test', Name='TestSLO', Description=None)
# TypeError: <class 'troposphere.applicationsignals.ServiceLevelObjective'>: test.Description is <class 'NoneType'>, expected <class 'str'>

# But omitting the property works fine:
excl_ok = ExclusionWindow(Window=window)  # Works
goal_ok = Goal()  # Works
slo_ok = ServiceLevelObjective('test', Name='TestSLO')  # Works
```

## Why This Is A Bug

This violates the expected behavior of optional properties. Users reasonably expect that `Class(optional_prop=None)` should behave identically to `Class()` when the property is optional. The current implementation forces users to use conditional logic to omit properties rather than passing None, making the API less ergonomic and breaking common patterns like passing nullable values from configuration or user input.

## Fix

The issue is in the `__setattr__` method of BaseAWSObject. It should check if the value is None and the property is optional before type validation:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -248,6 +248,12 @@ class BaseAWSObject:
             return None
         elif name in self.propnames:
+            # Allow None for optional properties
+            required = self.props[name][1]
+            if value is None and not required:
+                # Don't set the property at all for None on optional fields
+                return None
+            
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
```