# Bug Report: troposphere.validators.integer Inconsistent Error Handling for Infinity

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The integer validator function raises OverflowError instead of the expected ValueError when given infinity values, creating inconsistent error handling behavior.

## Property-Based Test

```python
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)),
    st.text(string.ascii_letters + string.punctuation),
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_rejects_invalid(value):
    try:
        int(value)
        assume(False)
    except (ValueError, TypeError):
        pass
    
    try:
        integer(value)
        assert False, f"Expected ValueError for {value}"
    except ValueError as e:
        assert "is not a valid integer" in str(e)
```

**Failing input**: `inf`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.validators import integer

result = integer(float('inf'))
```

## Why This Is A Bug

The integer validator is designed to raise ValueError with the message "is not a valid integer" for invalid inputs. However, when given infinity values, the internal `int()` call raises OverflowError which propagates uncaught. This creates inconsistent error handling where some invalid inputs raise ValueError while others raise OverflowError, violating the function's contract.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
        int(x)
+   except OverflowError:
+       raise ValueError("%r is not a valid integer" % x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```