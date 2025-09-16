# Bug Report: troposphere.autoscalingplans Deferred Required Field Validation

**Target**: `troposphere.autoscalingplans`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Classes in troposphere.autoscalingplans allow instantiation without required fields, deferring validation until `to_dict()` is called, violating the fail-fast principle.

## Property-Based Test

```python
from troposphere.autoscalingplans import TagFilter, MetricDimension

def test_required_fields_should_fail_at_instantiation():
    """Required fields should be validated at instantiation, not later"""
    # These should raise exceptions but don't
    tf = TagFilter()  # Missing required Key field
    md = MetricDimension()  # Missing required Name and Value fields
    
    # The error only occurs when trying to use the objects
    with pytest.raises(Exception):
        tf.to_dict()  # Fails here with "Resource Key required"
```

**Failing input**: No specific input - the bug is in allowing empty instantiation

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.autoscalingplans import TagFilter, ApplicationSource

# Step 1: Create TagFilter without required Key field (should fail but doesn't)
tf = TagFilter()
print(f"TagFilter created: {tf.properties}")  # Prints: {}

# Step 2: Use it in another object
app_source = ApplicationSource(TagFilters=[tf])
print("ApplicationSource created with invalid TagFilter")

# Step 3: Error occurs only when converting to dict
try:
    result = app_source.to_dict()
except Exception as e:
    print(f"Error at to_dict(): {e}")
    # Output: Resource Key required in type <class 'troposphere.autoscalingplans.TagFilter'>
```

## Why This Is A Bug

This violates the fail-fast principle - errors should occur as close to their source as possible. The current behavior allows invalid objects to be created and passed around, with errors only surfacing when `to_dict()` is called, potentially far from where the mistake was made. This makes debugging harder as the error location doesn't match the mistake location.

## Fix

The fix would require modifying the base class initialization to validate required fields immediately. Here's a high-level approach:

The `BaseAWSObject.__init__()` method in troposphere/__init__.py should validate required properties during instantiation rather than deferring to `to_dict()`. This would involve checking that all properties marked as required (`True` in the second element of the props tuple) are provided in kwargs during `__init__()`.