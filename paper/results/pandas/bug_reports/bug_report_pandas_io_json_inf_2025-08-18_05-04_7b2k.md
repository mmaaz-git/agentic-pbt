# Bug Report: pandas.io.json Column Name "INF" Converted to Float Infinity

**Target**: `pandas.read_json`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

`pandas.read_json` with orient='split' incorrectly converts the column name string "INF" to the float value infinity, corrupting column names.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas as pd
import io

@given(df=dataframes_strategy())
def test_json_roundtrip_split_orient(df):
    json_str = df.to_json(orient='split')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='split')
    
    pd.testing.assert_frame_equal(df, df_reconstructed)
```

**Failing input**: `df=pd.DataFrame({'INF': [0]})`

## Reproducing the Bug

```python
import pandas as pd
import io
import math

df = pd.DataFrame({'INF': [0]})
json_str = df.to_json(orient='split')
df_reconstructed = pd.read_json(io.StringIO(json_str), orient='split')

print(f"Original column: {df.columns[0]} (type: {type(df.columns[0])})")
print(f"JSON string: {json_str}")
print(f"Reconstructed column: {df_reconstructed.columns[0]} (type: {type(df_reconstructed.columns[0])})")
print(f"Column became infinity: {math.isinf(df_reconstructed.columns[0])}")
```

## Why This Is A Bug

The JSON specification clearly shows "INF" as a string in the columns array, but pandas incorrectly interprets it as the special float value infinity. This breaks the round-trip property and can cause serious issues in production systems where column names like "INF", "INFINITY", "NAN" might be legitimate identifiers (e.g., abbreviations for "Information", "Infrastructure", etc.).

## Fix

The JSON parser should not apply numeric/special value conversion to column names when they are clearly strings in the JSON structure.

```diff
# In pandas JSON parsing logic for split orient
- columns = [convert_special_values(col) for col in json_data['columns']]
+ columns = json_data['columns']  # Keep as strings, don't convert
```