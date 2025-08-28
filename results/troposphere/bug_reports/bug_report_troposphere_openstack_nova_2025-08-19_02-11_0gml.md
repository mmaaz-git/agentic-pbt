# Bug Report: troposphere.openstack.nova.Server Incorrect Key Access in validate()

**Target**: `troposphere.openstack.nova.Server.validate()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The Server.validate() method incorrectly accesses `self.resource["flavor_update_policy"]` when validating the `image_update_policy` attribute, causing a KeyError.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.openstack import nova

@given(
    image_update_policy=st.sampled_from(["REBUILD", "REPLACE", "REBUILD_PRESERVE_EPHEMERAL", "INVALID"])
)
def test_server_image_update_policy_validation_bug(image_update_policy):
    server = nova.Server("testserver", image="test-image", networks=[])
    server.resource["image_update_policy"] = image_update_policy
    
    if image_update_policy not in ["REBUILD", "REPLACE", "REBUILD_PRESERVE_EPHEMERAL"]:
        with pytest.raises(ValueError) as exc_info:
            server.validate()
        assert "image_update_policy" in str(exc_info.value)
    else:
        server.validate()  # Should not raise
```

**Failing input**: `image_update_policy='REBUILD'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.openstack import nova

server = nova.Server("testserver", image="test-image", networks=[])
server.resource["image_update_policy"] = "REBUILD"
server.validate()
```

## Why This Is A Bug

The validate() method should check if `image_update_policy` is valid, but on line 143 of nova.py, it incorrectly accesses `self.resource["flavor_update_policy"]` instead of `self.resource["image_update_policy"]`. This causes a KeyError when `image_update_policy` is set but `flavor_update_policy` is not.

## Fix

```diff
--- a/troposphere/openstack/nova.py
+++ b/troposphere/openstack/nova.py
@@ -140,7 +140,7 @@ class Server(AWSObject):
                 )
 
         if "image_update_policy" in self.resource:
-            image_update_policy = self.resource["flavor_update_policy"]
+            image_update_policy = self.resource["image_update_policy"]
             if image_update_policy not in [
                 "REBUILD",
                 "REPLACE",
```