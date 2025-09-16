# Bug Report: troposphere.imagebuilder Integer Validator Crashes on Float Infinity

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The integer validator in troposphere crashes with an unhandled OverflowError when passed float infinity or negative infinity values, causing application failure instead of proper validation error.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.imagebuilder as ib

@given(
    volume_size=st.floats(allow_nan=True, allow_infinity=True)
)
def test_ebs_volume_size_with_floats(volume_size):
    """Test EBS VolumeSize property with float values including infinity"""
    ebs = ib.EbsInstanceBlockDeviceSpecification()
    try:
        ebs.VolumeSize = volume_size
        # If accepted, should be convertible to int
        assert isinstance(int(ebs.VolumeSize), int)
    except (TypeError, ValueError):
        # Expected for invalid float values
        pass
    except OverflowError:
        # This should not happen - should be caught and converted to ValueError
        raise AssertionError(f"Unhandled OverflowError for value: {volume_size}")
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.imagebuilder as ib

ebs = ib.EbsInstanceBlockDeviceSpecification()
ebs.VolumeSize = float('inf')
```

## Why This Is A Bug

The integer validator function is supposed to validate integer inputs and raise a ValueError for invalid inputs. However, it doesn't handle the OverflowError that occurs when `int()` is called on float infinity. This causes an unhandled exception to propagate to the user instead of a proper validation error. The validator catches ValueError and TypeError but misses OverflowError, violating the expected error handling contract.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,7 +46,7 @@
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```