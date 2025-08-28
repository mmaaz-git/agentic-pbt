# Bug Report: troposphere.openstack.neutron.SessionPersistence Incorrect Validation Logic

**Target**: `troposphere.openstack.neutron.SessionPersistence.validate()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The SessionPersistence.validate() method incorrectly requires `cookie_name` for all session types, not just for `APP_COOKIE` type as intended.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.openstack import neutron

@given(
    session_type=st.sampled_from(["SOURCE_IP", "HTTP_COOKIE", "APP_COOKIE"]),
    has_cookie_name=st.booleans()
)
def test_session_persistence_validation_logic(session_type, has_cookie_name):
    props = {"type": session_type}
    if has_cookie_name:
        props["cookie_name"] = "test_cookie"
    
    session = neutron.SessionPersistence(**props)
    
    if session_type == "APP_COOKIE" and not has_cookie_name:
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "cookie_name" in str(exc_info.value)
    else:
        session.validate()  # Should not raise for SOURCE_IP or HTTP_COOKIE without cookie_name
```

**Failing input**: `session_type='SOURCE_IP', has_cookie_name=False`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.openstack import neutron

session = neutron.SessionPersistence(type="SOURCE_IP")
session.validate()
```

## Why This Is A Bug

The validation logic checks if `type` exists in the resource, then immediately checks if `cookie_name` is missing and raises an error. However, `cookie_name` should only be required when `type` is `APP_COOKIE`, not for `SOURCE_IP` or `HTTP_COOKIE` types.

## Fix

```diff
--- a/troposphere/openstack/neutron.py
+++ b/troposphere/openstack/neutron.py
@@ -126,11 +126,12 @@ class SessionPersistence(AWSProperty):
 
     def validate(self):
         if "type" in self.resource:
-            if "cookie_name" not in self.resource:
+            session_type = self.resource["type"]
+            
+            if session_type == "APP_COOKIE" and "cookie_name" not in self.resource:
                 raise ValueError(
                     "The cookie_name attribute must be "
                     "given if session type is APP_COOKIE"
                 )
 
-            session_type = self.resource["type"]
             if session_type not in ["SOURCE_IP", "HTTP_COOKIE", "APP_COOKIE"]:
```