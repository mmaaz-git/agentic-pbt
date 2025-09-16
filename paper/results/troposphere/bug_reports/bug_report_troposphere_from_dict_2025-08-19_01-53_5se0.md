# Bug Report: troposphere _from_dict Method Fails Without Title

**Target**: `troposphere.BaseAWSObject._from_dict`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `_from_dict` class method fails when creating objects without providing a title, breaking round-trip serialization for objects that don't require titles.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.iotwireless as iotwireless

@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=100),
    st.sampled_from(["RuleName", "SnsTopic", "MqttTopic"])
)
def test_from_dict_round_trip(name, expression, expr_type):
    """Test round-trip: dict -> object -> dict preserves data."""
    original_dict = {
        "Expression": expression,
        "ExpressionType": expr_type,
        "Name": name
    }
    
    obj = iotwireless.Destination._from_dict(**original_dict)
    result_dict = obj.to_dict(validation=False)
    
    props = result_dict.get("Properties", result_dict)
    assert props["Expression"] == expression
```

**Failing input**: Any valid property dictionary without title

## Reproducing the Bug

```python
import troposphere.iotwireless as iotwireless

obj = iotwireless.Destination._from_dict(
    Expression="test",
    ExpressionType="RuleName",
    Name="TestDest"
)
```

## Why This Is A Bug

The `_from_dict` method is designed to create objects from dictionaries, which is essential for deserialization. However, it fails when no title is provided, even though titles are optional in many contexts. This breaks the round-trip property where an object can be converted to a dict and back.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -400,5 +400,5 @@
         props[prop_name] = value
     if title:
         return cls(title, **props)
-    return cls(**props)
+    return cls(None, **props)  # Pass None as title when not provided
```