# Bug Report: pandas.io.json Float64 Dtype Lost for Zero Values

**Target**: `pandas.read_json`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

`pandas.read_json` incorrectly infers int64 dtype for columns containing only 0.0 float values, losing the original float64 dtype information.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas as pd
import io

@given(df=dataframes_strategy())
def test_json_roundtrip_records_orient(df):
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    pd.testing.assert_frame_equal(df.reset_index(drop=True), df_reconstructed.reset_index(drop=True))
```

**Failing input**: `df=pd.DataFrame({'A': [0], 'B': [0], 'C': [0], 'D': [0], 'E': [0], 'F': [0], 'G': [0], 'H': [0.0]})`

## Reproducing the Bug

```python
import pandas as pd
import io

df = pd.DataFrame({
    'int_col': [0, 0, 0],
    'float_col': [0.0, 0.0, 0.0]
})

print(f"Original dtypes:\n{df.dtypes}")

json_str = df.to_json(orient='records')
print(f"\nJSON representation:\n{json_str}")

df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
print(f"\nReconstructed dtypes:\n{df_reconstructed.dtypes}")

assert df['float_col'].dtype == df_reconstructed['float_col'].dtype, "Float dtype was lost!"
```

## Why This Is A Bug

JSON preserves the distinction between integer 0 and float 0.0, but pandas' type inference incorrectly converts float 0.0 values to integers when all values in a column are zero. This breaks the round-trip property and can cause issues in numerical computations where float precision is required, or when the dtype carries semantic meaning (e.g., sensor readings that should remain floats even when zero).

## Fix

The JSON parser should respect the numeric type indicated in the JSON representation rather than applying aggressive type inference.

```diff
# In pandas JSON type inference logic
- if all values can be represented as integers:
-     return int64_dtype
+ if value in json is 0.0 (with decimal point):
+     preserve float64_dtype
+ elif value in json is 0 (without decimal):
+     use int64_dtype
```