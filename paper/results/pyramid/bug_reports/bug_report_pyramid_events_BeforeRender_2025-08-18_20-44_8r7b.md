# Bug Report: pyramid.events.BeforeRender Attribute/Dictionary Key Conflict

**Target**: `pyramid.events.BeforeRender`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `BeforeRender` class has a naming conflict where `rendering_val` can simultaneously exist as both a dictionary key and an instance attribute with different values, violating the principle of least surprise.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.events import BeforeRender

@given(
    dict_value=st.text(),
    param_value=st.text()
)
def test_rendering_val_conflict(dict_value, param_value):
    """Test that rendering_val behaves consistently"""
    if dict_value == param_value:
        return  # Skip when values are same
    
    system_dict = {'rendering_val': dict_value}
    event = BeforeRender(system_dict, rendering_val=param_value)
    
    # These should reasonably be expected to be the same
    assert event['rendering_val'] == event.rendering_val
```

**Failing input**: `dict_value='value_from_dict', param_value='value_from_param'`

## Reproducing the Bug

```python
from pyramid.events import BeforeRender

system_dict = {
    'rendering_val': 'value_from_dict',
    'other_key': 'other_value'
}

event = BeforeRender(system_dict, rendering_val='value_from_param')

print(f"event['rendering_val'] = {event['rendering_val']}")
print(f"event.rendering_val = {event.rendering_val}")

assert event['rendering_val'] != event.rendering_val
```

## Why This Is A Bug

This violates the principle of least surprise. Users would reasonably expect that accessing `rendering_val` would return the same value regardless of whether they use dictionary-style access (`event['rendering_val']`) or attribute access (`event.rendering_val`). The current behavior allows these to be different values, which can lead to subtle bugs and confusion in code that uses `BeforeRender`.

The documentation states that BeforeRender "has a dictionary-like interface" and that the `rendering_val` attribute provides access to the rendering value. However, it doesn't warn that if the system dictionary contains a key named `'rendering_val'`, there will be a conflict between the dictionary key and the attribute.

## Fix

```diff
--- a/pyramid/events.py
+++ b/pyramid/events.py
@@ -300,5 +300,11 @@ class BeforeRender(dict):
 
     def __init__(self, system, rendering_val=None):
         dict.__init__(self, system)
+        # Prevent conflict between dict key and attribute
+        if 'rendering_val' in self:
+            import warnings
+            warnings.warn(
+                "The system dict contains a 'rendering_val' key which conflicts "
+                "with the BeforeRender.rendering_val attribute. Consider using a different key name.",
+                UserWarning)
         self.rendering_val = rendering_val
```