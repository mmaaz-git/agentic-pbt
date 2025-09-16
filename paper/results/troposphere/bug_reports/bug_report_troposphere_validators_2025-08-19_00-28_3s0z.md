# Bug Report: troposphere.validators network_port Error Message Inconsistency

**Target**: `troposphere.validators.network_port`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The network_port validator accepts -1 as a valid port number but the error message incorrectly states ports must be "between 0 and 65535", creating misleading documentation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import validators

@given(st.integers())
def test_network_port_validator_range(port):
    if -1 <= port <= 65535:
        result = validators.network_port(port)
        assert result == port
    else:
        with pytest.raises(ValueError, match="network port .* must been between 0 and 65535"):
            validators.network_port(port)
```

**Failing input**: The error message itself is incorrect when port = -2

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import validators

# -1 is accepted as valid
result = validators.network_port(-1)
print(f"network_port(-1) = {result}")  # Returns -1

# -2 is rejected with misleading error message
try:
    validators.network_port(-2)
except ValueError as e:
    print(f"Error for -2: {e}")
    # Error says "between 0 and 65535" but -1 is valid!

print("\nActual valid range: -1 to 65535")
print("Error message claims: 0 to 65535")
```

## Why This Is A Bug

The error message provides incorrect documentation about the valid range of port numbers. The validator correctly accepts -1 (which has special meaning in some contexts as "any port"), but the error message doesn't reflect this, potentially confusing users about what values are acceptable.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -128,7 +128,7 @@ def network_port(x: Any) -> Union[AWSHelperFn, str, bytes, SupportsInt, Support
 
     i = integer(x)
     if int(i) < -1 or int(i) > 65535:
-        raise ValueError("network port %r must been between 0 and 65535" % i)
+        raise ValueError("network port %r must be between -1 and 65535" % i)
     return x
```