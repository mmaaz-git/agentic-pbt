# Bug Report: pandas.io.json String-to-Integer Misinterpretation

**Target**: `pandas.read_json`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

`pandas.read_json` incorrectly converts string values consisting entirely of zeros to the integer 0, causing data corruption when reading JSON containing such strings.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas as pd
import io

@given(
    long_string=st.text(min_size=1000, max_size=5000)
)
def test_long_strings_json(long_string):
    df = pd.DataFrame({'long_text': [long_string]})
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    assert df['long_text'].iloc[0] == df_reconstructed['long_text'].iloc[0]
```

**Failing input**: `long_string='0' * 1000`

## Reproducing the Bug

```python
import pandas as pd
import io

df = pd.DataFrame({'long_text': ['0' * 1000]})
json_str = df.to_json(orient='records')
df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')

print(f"Original type: {type(df['long_text'].iloc[0])}")
print(f"Original value (truncated): {df['long_text'].iloc[0][:20]}...")
print(f"Reconstructed type: {type(df_reconstructed['long_text'].iloc[0])}")
print(f"Reconstructed value: {df_reconstructed['long_text'].iloc[0]}")
```

## Why This Is A Bug

This violates the fundamental round-trip property of serialization: `deserialize(serialize(data)) == data`. A string of zeros is semantically different from the integer 0. This bug causes silent data corruption where string data is lost and replaced with incorrect numeric values. Applications relying on JSON serialization for data persistence or transmission will experience data loss.

## Fix

The issue appears to be in the JSON parser's type inference logic, which incorrectly interprets strings of zeros as numeric values. The parser should respect the JSON string type and not attempt numeric conversion on string literals.

```diff
# In pandas/io/json/_json.py or similar location
# The parser should check if the value was originally a string in JSON
- if looks_like_number(value):
-     return convert_to_number(value)
+ if isinstance(value, str) and value_was_json_string:
+     return value
+ elif looks_like_number(value):
+     return convert_to_number(value)
```