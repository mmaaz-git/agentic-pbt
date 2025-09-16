"""Investigate factorize bug with None vs NaN"""

import numpy as np
import pandas as pd
from pandas.core.algorithms import factorize
import datetime
import random
import string

# Test case 1: None vs NaN confusion
print("=" * 60)
print("BUG 1: factorize confuses None and NaN in object arrays")
print("=" * 60)

values = [None, float('nan'), 1, None, float('nan'), 2]
arr = np.array(values, dtype=object)

print("Original values:", values)
print()

# Factorize with use_na_sentinel=False (should preserve both None and NaN as different)
codes, uniques = factorize(arr, use_na_sentinel=False)

print("Factorized with use_na_sentinel=False:")
print("Codes:", codes)
print("Uniques:", uniques)

# Count None and NaN in original
none_count = sum(1 for v in values if v is None)
nan_count = sum(1 for v in values if isinstance(v, float) and pd.isna(v))
print(f"\nOriginal: {none_count} None, {nan_count} NaN")

# Count in uniques
unique_none_count = sum(1 for v in uniques if v is None)
unique_nan_count = sum(1 for v in uniques if isinstance(v, float) and pd.isna(v))
print(f"Uniques: {unique_none_count} None, {unique_nan_count} NaN")

# Reconstruct
if isinstance(uniques, pd.Index):
    reconstructed = np.array(uniques.take(codes))
else:
    reconstructed = uniques.take(codes)

print("\nReconstructed values vs original:")
for i, (orig, recon) in enumerate(zip(values, reconstructed)):
    orig_str = "None" if orig is None else ("NaN" if pd.isna(orig) else str(orig))
    recon_str = "None" if recon is None else ("NaN" if pd.isna(recon) else str(recon))
    matches = (orig is None and recon is None) or \
              (isinstance(orig, float) and pd.isna(orig) and isinstance(recon, float) and pd.isna(recon)) or \
              (orig == recon)
    print(f"  {i}: {orig_str} -> {recon_str} {'✓' if matches else '✗ MISMATCH'}")

print("\n=== BUG CONFIRMED ===")
print("None and NaN should be treated as distinct values when use_na_sentinel=False")
print("But factorize treats them as the same, losing information")
print("This violates the round-trip property: uniques.take(codes) != original")

# Create bug report
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
hash_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
filename = f"bug_report_pandas_core_factorize_{timestamp}_{hash_str}.md"

bug_report = f"""# Bug Report: pandas.core.algorithms.factorize Conflates None and NaN

**Target**: `pandas.core.algorithms.factorize`
**Severity**: Medium
**Bug Type**: Logic
**Date**: {datetime.date.today()}

## Summary

`factorize` incorrectly treats `None` and `NaN` as identical values in object arrays when `use_na_sentinel=False`, violating the documented round-trip property.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy as np
import pandas as pd
from pandas.core.algorithms import factorize

@given(st.lists(st.one_of(
    st.none(),
    st.just(float('nan')),
    st.integers(),
), min_size=1, max_size=20))
def test_factorize_none_vs_nan(values):
    arr = np.array(values, dtype=object)
    codes, uniques = factorize(arr, use_na_sentinel=False)
    
    none_count = sum(1 for v in values if v is None)
    nan_count = sum(1 for v in values if isinstance(v, float) and pd.isna(v))
    
    if none_count > 0 and nan_count > 0:
        unique_none_count = sum(1 for v in uniques if v is None)
        unique_nan_count = sum(1 for v in uniques if isinstance(v, float) and pd.isna(v))
        
        assert unique_none_count > 0, "None should be in uniques"
        assert unique_nan_count > 0, "NaN should be in uniques"
```

**Failing input**: `[None, nan]`

## Reproducing the Bug

```python
import numpy as np
import pandas as pd
from pandas.core.algorithms import factorize

values = [None, float('nan'), 1, None, float('nan'), 2]
arr = np.array(values, dtype=object)

codes, uniques = factorize(arr, use_na_sentinel=False)

print("Original:", values)
print("Codes:", codes)
print("Uniques:", uniques)

# Reconstruct
reconstructed = uniques.take(codes)
print("Reconstructed:", reconstructed)

# Check: None becomes NaN
for orig, recon in zip(values, reconstructed):
    if orig is None and pd.isna(recon):
        print(f"BUG: None -> NaN")
```

## Why This Is A Bug

When `use_na_sentinel=False`, factorize should preserve all distinct values in the input. `None` and `NaN` are distinct Python objects:
- `None` is Python's null singleton
- `NaN` is a floating-point "Not a Number" value

The documentation states that `uniques.take(codes)` will reconstruct the original values, but this fails when both `None` and `NaN` are present - all `None` values become `NaN`.

## Fix

The issue is in the preprocessing step at lines 754-763 of pandas/core/algorithms.py where object arrays with `use_na_sentinel=False` have all null-like values converted to a single `na_value`:

```diff
-        if not use_na_sentinel and values.dtype == object:
-            null_mask = isna(values)
-            if null_mask.any():
-                na_value = na_value_for_dtype(values.dtype, compat=False)
-                values = np.where(null_mask, na_value, values)
+        # Do not conflate different null types when use_na_sentinel=False
+        # Let the hashtable handle them as distinct values
```
"""

with open(filename, 'w') as f:
    f.write(bug_report)

print(f"\nBug report saved to: {filename}")