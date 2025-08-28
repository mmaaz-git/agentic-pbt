# Bug Report: coremltools.optimize._utils Invalid Quantization Range

**Target**: `coremltools.optimize._utils.get_quant_range`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `get_quant_range` function returns an invalid range [0, 0] for 1-bit quantization with LINEAR_SYMMETRIC mode, which would cause division by zero in quantization operations.

## Property-Based Test

```python
@given(
    nbits=st.integers(min_value=1, max_value=16),
    signed=st.booleans()
)
def test_quant_range_validity(nbits, signed):
    """Test that quantization ranges are valid and consistent"""
    for mode in ["LINEAR", "LINEAR_SYMMETRIC"]:
        min_val, max_val = get_quant_range(nbits, signed, mode)
        
        # Basic range checks
        assert min_val < max_val  # This fails!
        assert isinstance(min_val, int)
        assert isinstance(max_val, int)
```

**Failing input**: `nbits=1, signed=False, mode="LINEAR_SYMMETRIC"` and `nbits=1, signed=True, mode="LINEAR_SYMMETRIC"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')
from coremltools.optimize._utils import get_quant_range

# Case 1: Unsigned 1-bit LINEAR_SYMMETRIC
min_val, max_val = get_quant_range(1, False, "LINEAR_SYMMETRIC")
print(f"Unsigned 1-bit LINEAR_SYMMETRIC: [{min_val}, {max_val}]")
assert min_val < max_val, f"Invalid range: [{min_val}, {max_val}]"

# Case 2: Signed 1-bit LINEAR_SYMMETRIC  
min_val, max_val = get_quant_range(1, True, "LINEAR_SYMMETRIC")
print(f"Signed 1-bit LINEAR_SYMMETRIC: [{min_val}, {max_val}]")
assert min_val < max_val, f"Invalid range: [{min_val}, {max_val}]"
```

## Why This Is A Bug

A quantization range must have at least two distinct values to represent data variation. The range [0, 0] cannot represent any quantization levels and would cause division by zero when computing scale factors in quantization operations. The formula `scale = (val_max - val_min) / (q_val_max - q_val_min)` would have a zero denominator.

## Fix

```diff
--- a/coremltools/optimize/_utils.py
+++ b/coremltools/optimize/_utils.py
@@ -45,6 +45,10 @@ def get_quant_range(n_bits: int, signed: bool, mode: str) -> Tuple[int, int]:
     """
     Utility to get the quantization range for a given quantization config
     Adapted from phoenix/quatization/_utils.py
     """
+    # 1-bit quantization with LINEAR_SYMMETRIC is not meaningful
+    if n_bits == 1 and mode == "LINEAR_SYMMETRIC":
+        raise ValueError("1-bit quantization with LINEAR_SYMMETRIC mode is not supported")
+    
     max_q = 2**n_bits
     if not signed:
         quant_min = 0
```