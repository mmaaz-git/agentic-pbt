# Bug Report: json.loads parse_float Parameter Not Called for Special Float Values

**Target**: `json.loads`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `parse_float` parameter of `json.loads` is not called for the special float values `Infinity`, `-Infinity`, and `NaN`, contrary to its documentation which states it "will be called with the string of every JSON float to be decoded."

## Property-Based Test

```python
import json
from hypothesis import given, strategies as st


@given(st.sampled_from(['Infinity', '-Infinity', 'NaN', '3.14', '1e10']))
def test_parse_float_called_for_all_floats(json_str):
    calls = []
    
    def track_parse_float(s):
        calls.append(s)
        return float(s)
    
    result = json.loads(json_str, parse_float=track_parse_float)
    
    # parse_float should be called for all float values
    if json_str in ['Infinity', '-Infinity', 'NaN']:
        # BUG: parse_float is NOT called for these special values
        assert len(calls) == 0  # Current behavior
        # assert len(calls) == 1  # Expected behavior
    else:
        assert len(calls) == 1  # Works correctly for regular floats
```

**Failing input**: `'Infinity'`, `'-Infinity'`, `'NaN'`

## Reproducing the Bug

```python
import json

def custom_parse_float(s):
    print(f"parse_float called with: {s}")
    return f"CUSTOM_{s}"

# Regular float - parse_float IS called
result = json.loads('3.14', parse_float=custom_parse_float)
print(f"3.14 -> {result}")

# Special values - parse_float is NOT called
result = json.loads('Infinity', parse_float=custom_parse_float)
print(f"Infinity -> {result}")

result = json.loads('NaN', parse_float=custom_parse_float)
print(f"NaN -> {result}")
```

## Why This Is A Bug

The documentation for `parse_float` states: "parse_float, if specified, will be called with the string of every JSON float to be decoded." The values `Infinity`, `-Infinity`, and `NaN` are floating-point values in JSON (even though they're not standard JSON), yet `parse_float` is not called for them. Instead, they are handled by the `parse_constant` parameter.

This inconsistency makes it impossible to use `parse_float` to uniformly handle all floating-point values, which could be important for applications that need custom float parsing (e.g., using `Decimal` for all numeric values).

## Fix

The issue is an API design/documentation mismatch rather than a code bug. Possible fixes:

1. **Documentation fix** (recommended): Update the `parse_float` documentation to clarify that it handles numeric floats but not the special constants `Infinity`, `-Infinity`, and `NaN`, which are handled by `parse_constant`.

2. **Code fix** (breaking change): Modify the JSON decoder to pass `Infinity`, `-Infinity`, and `NaN` to `parse_float` instead of `parse_constant`. This would be a breaking change for existing code that relies on the current behavior.

The documentation should be updated to:
```
parse_float, if specified, will be called with the string of every JSON
numeric float to be decoded (but not the special constants Infinity,
-Infinity, or NaN, which are handled by parse_constant).
```