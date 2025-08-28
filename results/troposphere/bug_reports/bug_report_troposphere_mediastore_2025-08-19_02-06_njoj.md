# Bug Report: troposphere.mediastore Stderr Pollution on Validation Error

**Target**: `troposphere.mediastore.MetricPolicy` (affects all troposphere validation)
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Troposphere writes error messages to stderr before raising validation exceptions, causing stderr pollution even when exceptions are properly handled.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sys, io
from contextlib import redirect_stderr
from troposphere.mediastore import MetricPolicy

@given(st.text().filter(lambda x: x not in ["DISABLED", "ENABLED"]))
def test_validation_no_stderr_pollution(invalid_status):
    """Validation errors should not write to stderr when raising exceptions."""
    captured_stderr = io.StringIO()
    
    with redirect_stderr(captured_stderr):
        try:
            policy = MetricPolicy(ContainerLevelMetrics=invalid_status)
        except ValueError:
            pass  # Exception properly handled
    
    stderr_output = captured_stderr.getvalue()
    assert not stderr_output, f"Library polluted stderr: {stderr_output}"
```

**Failing input**: Any string not in `["DISABLED", "ENABLED"]`, e.g., `"INVALID"`

## Reproducing the Bug

```python
import sys, io
from contextlib import redirect_stderr

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.mediastore import MetricPolicy

captured_stderr = io.StringIO()

with redirect_stderr(captured_stderr):
    try:
        policy = MetricPolicy(ContainerLevelMetrics="INVALID")
    except ValueError:
        pass

stderr_output = captured_stderr.getvalue()
print(f"Stderr pollution: {repr(stderr_output)}")
```

## Why This Is A Bug

Libraries should not write to stderr/stdout unless explicitly configured to do so. This behavior:
1. Pollutes application logs with redundant error messages
2. Makes testing harder as stderr gets cluttered with expected validation failures
3. Violates the principle that exceptions should be the primary error signaling mechanism
4. The error message provides no additional information beyond what's in the exception

## Fix

The issue is in `/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/troposphere/__init__.py` lines 267-271:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -264,11 +264,6 @@ class BaseAWSObject:
             elif isinstance(expected_type, types.FunctionType):
                 try:
                     value = expected_type(value)
                 except Exception:
-                    sys.stderr.write(
-                        "%s: %s.%s function validator '%s' threw "
-                        "exception:\n"
-                        % (self.__class__, self.title, name, expected_type.__name__)
-                    )
                     raise
                 return self.properties.__setitem__(name, value)
```