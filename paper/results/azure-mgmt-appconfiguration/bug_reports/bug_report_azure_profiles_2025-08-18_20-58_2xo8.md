# Bug Report: azure.profiles ProfileDefinition Allows External Mutation of Internal State

**Target**: `azure.profiles.ProfileDefinition`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

ProfileDefinition class in azure.profiles fails to protect its internal dictionary from external modification, allowing runtime mutation of supposedly immutable profile configurations including pre-defined KnownProfiles.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import copy
from azure.profiles import ProfileDefinition

@given(
    initial_dict=st.dictionaries(
        keys=st.text(min_size=1, max_size=50).filter(lambda x: '.' in x),
        values=st.dictionaries(
            keys=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
            values=st.text(min_size=1, max_size=30),
            min_size=1,
            max_size=3
        ),
        min_size=1,
        max_size=5
    ),
    label=st.text(min_size=1, max_size=50)
)
def test_profile_definition_encapsulation_violation(initial_dict, label):
    original_state = copy.deepcopy(initial_dict)
    profile = ProfileDefinition(initial_dict, label)
    returned_dict = profile.get_profile_dict()
    
    if returned_dict:
        returned_dict["INJECTED_KEY"] = {"injected": "value"}
        current_dict = profile.get_profile_dict()
        assert "INJECTED_KEY" in current_dict
        
        initial_dict["ANOTHER_INJECTION"] = {"also": "injected"}
        final_dict = profile.get_profile_dict()
        assert "ANOTHER_INJECTION" in final_dict
```

**Failing input**: `initial_dict={'a.b': {None: 'v1'}}`, `label='test'`

## Reproducing the Bug

```python
from azure.profiles import ProfileDefinition, KnownProfiles

# Example 1: User-created ProfileDefinition
original_dict = {"azure.test.Client": {None: "2021-01-01"}}
profile = ProfileDefinition(original_dict, "test-profile")

returned_dict = profile.get_profile_dict()
returned_dict["INJECTED_CLIENT"] = {None: "HACKED"}

assert profile.get_profile_dict()["INJECTED_CLIENT"] == {None: "HACKED"}
print("Bug: External modification affected ProfileDefinition")

# Example 2: Pre-defined KnownProfiles can be modified
profile_dict = KnownProfiles.v2020_09_01_hybrid.value.get_profile_dict()
profile_dict["INJECTED_CLIENT"] = {None: "HACKED"}

assert "INJECTED_CLIENT" in KnownProfiles.v2020_09_01_hybrid.value.get_profile_dict()
print("Bug: Pre-defined KnownProfiles modified at runtime!")
```

## Why This Is A Bug

This violates fundamental encapsulation principles and creates serious issues:

1. **Security Risk**: Malicious code can modify profile definitions to redirect API calls to unauthorized versions
2. **Data Integrity**: Profile definitions that should be immutable constants can be changed at runtime
3. **Thread Safety**: Concurrent modifications to shared profile objects can cause race conditions
4. **Debugging Difficulty**: Profile definitions can change unexpectedly during execution, making bugs hard to trace

The ProfileDefinition class is designed to store API version mappings that should remain constant after creation. The ability to modify these mappings externally breaks this contract.

## Fix

```diff
--- a/azure/profiles/__init__.py
+++ b/azure/profiles/__init__.py
@@ -4,6 +4,7 @@
 # license information.
 #--------------------------------------------------------------------------
 from enum import Enum
+import copy
 
 class ProfileDefinition(object):
     """Allow to define a custom Profile definition.
@@ -17,8 +18,8 @@ class ProfileDefinition(object):
     :param str label: A label for pretty printing
     """
     def __init__(self, profile_dict, label=None):
-        self._profile_dict = profile_dict
-        self._label = label
+        self._profile_dict = copy.deepcopy(profile_dict) if profile_dict else profile_dict
+        self._label = label
 
     @property
     def label(self):
@@ -34,7 +35,7 @@ class ProfileDefinition(object):
 
         This is internal information, and content should not be considered stable.
         """
-        return self._profile_dict
+        return copy.deepcopy(self._profile_dict) if self._profile_dict else self._profile_dict
```