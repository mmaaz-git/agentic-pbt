# Bug Report: troposphere.validators.network_port Error Message Issues

**Target**: `troposphere.validators.network_port`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `network_port` function has two issues in its error message: (1) grammatical error "must been" instead of "must be", and (2) incorrect range specification saying "between 0 and 65535" when -1 is actually valid.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import network_port

@given(st.integers().filter(lambda x: x < -1 or x > 65535))
def test_network_port_error_message(port):
    """Test that network_port error message is correct"""
    try:
        network_port(port)
        assert False, f"Should have raised ValueError for port {port}"
    except ValueError as e:
        error_msg = str(e)
        # Check for typo
        assert "must been" not in error_msg, f"Error message has typo: {error_msg}"
        # Check for correct range
        assert "between -1 and 65535" in error_msg or "from -1 to 65535" in error_msg, \
            f"Error message has wrong range (should mention -1 is valid): {error_msg}"
```

**Failing input**: Any invalid port like `70000` or `-2`

## Reproducing the Bug

```python
from troposphere.validators import network_port

# -1 is actually valid
network_port(-1)  # Returns -1 (success)

# But the error message says "between 0 and 65535"
network_port(-2)  
# ValueError: network port -2 must been between 0 and 65535
#                                  ^^^^            ^
#                    Should be "must be"      Should be "-1"
```

## Why This Is A Bug

1. **Grammatical error**: "must been" should be "must be"
2. **Incorrect range documentation**: The error says ports must be "between 0 and 65535" but the code actually accepts -1 as valid (likely for special cases like dynamic port allocation)

This creates confusion for users who might think -1 is invalid based on the error message.

## Fix

```diff
def network_port(x: Any) -> Union[AWSHelperFn, str, bytes, SupportsInt, SupportsIndex]:
    from .. import AWSHelperFn

    # Network ports can be Ref items
    if isinstance(x, AWSHelperFn):
        return x

    i = integer(x)
    if int(i) < -1 or int(i) > 65535:
-       raise ValueError("network port %r must been between 0 and 65535" % i)
+       raise ValueError("network port %r must be between -1 and 65535" % i)
    return x
```