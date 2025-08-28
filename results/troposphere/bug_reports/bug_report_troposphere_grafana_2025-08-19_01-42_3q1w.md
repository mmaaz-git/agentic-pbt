# Bug Report: troposphere.validators.boolean Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean` validator function incorrectly accepts float values 0.0 and 1.0, converting them to False and True respectively, when it should only accept specific integer and string values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Test that boolean validator rejects all float inputs."""
    try:
        result = boolean(value)
        assert False, f"boolean({value!r}) should have raised ValueError but returned {result!r}"
    except ValueError:
        pass  # Expected behavior
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

# These should raise ValueError but don't
print(boolean(0.0))  # Returns False
print(boolean(1.0))  # Returns True

# This affects actual Grafana resources
import troposphere.grafana as grafana

workspace = grafana.Workspace(
    title="TestWorkspace",
    AccountAccessType="CURRENT_ACCOUNT", 
    AuthenticationProviders=["AWS_SSO"],
    PermissionType="SERVICE_MANAGED",
    PluginAdminEnabled=1.0  # Float accepted when boolean expected
)

print(workspace.to_dict()["Properties"]["PluginAdminEnabled"])  # Outputs: True
```

## Why This Is A Bug

The boolean validator is documented to accept only specific values: `True`, `False`, integers 0 and 1, and strings "0", "1", "true", "True", "false", "False". However, due to Python's equality behavior where `0.0 == 0` and `1.0 == 1`, the current implementation using the `in` operator inadvertently accepts float values. This violates the type contract and could lead to unexpected behavior when non-boolean float values are passed to boolean properties in CloudFormation templates.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,10 +36,17 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    # Check for exact boolean types first
+    if x is True:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False:
         return False
+    # Check for integer types (but not float)
+    if isinstance(x, int) and not isinstance(x, bool):
+        if x == 1:
+            return True
+        if x == 0:
+            return False
+    # Check for string types
+    if isinstance(x, str) and x in ["1", "true", "True", "0", "false", "False"]:
+        return x in ["1", "true", "True"]
     raise ValueError
```