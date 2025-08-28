# Bug Report: troposphere.kendra Type Preservation in Integer Validator

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The integer validator accepts string representations of integers but doesn't convert them to actual integers, causing type inconsistency in CloudFormation templates and preserving problematic formatting like leading zeros.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer
import troposphere.kendra as kendra
import json

@given(st.integers(min_value=1, max_value=999))
def test_string_numbers_with_leading_zeros(num):
    """String numbers with leading zeros are preserved incorrectly"""
    str_with_zeros = "00" + str(num)
    
    result = integer(str_with_zeros)
    assert result == str_with_zeros  # "00123" preserved as-is
    
    config = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=str_with_zeros,
        StorageCapacityUnits=num
    )
    
    cf_dict = config.to_dict()
    # Produces mixed types and wrong values
    assert cf_dict['QueryCapacityUnits'] == str_with_zeros  # "00123" 
    assert cf_dict['StorageCapacityUnits'] == num  # 123
    assert int(cf_dict['QueryCapacityUnits']) != cf_dict['QueryCapacityUnits']
```

**Failing input**: String "010" vs integer 10

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
import troposphere.kendra as kendra
import json

config = kendra.CapacityUnitsConfiguration(
    QueryCapacityUnits="010",
    StorageCapacityUnits=10
)

result = config.to_dict()
print(f"QueryCapacityUnits: {repr(result['QueryCapacityUnits'])} (type: {type(result['QueryCapacityUnits']).__name__})")
print(f"StorageCapacityUnits: {repr(result['StorageCapacityUnits'])} (type: {type(result['StorageCapacityUnits']).__name__})")

cf_json = json.dumps(result)
print(f"CloudFormation JSON: {cf_json}")

print(f"\nProblem: '010' != 10, and CloudFormation expects integers not strings")
```

## Why This Is A Bug

CloudFormation expects integer properties to be JSON numbers, not strings. The current behavior:
1. Creates type-inconsistent templates (mixing strings and integers)
2. Preserves leading zeros which changes the semantic value
3. Can cause arithmetic operations to fail (string concatenation vs numeric addition)
4. Violates the principle of "parse, don't validate"

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
-       int(x)
+       # Convert to integer to ensure consistent type
+       return int(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
-   else:
-       return x
```