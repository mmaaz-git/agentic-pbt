# Bug Report: scipy.signal.windows.tukey Incorrect Hann Equivalence for Small Windows

**Target**: `scipy.signal.windows.tukey`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The Tukey window with alpha=1.0 does not match the Hann window for small window sizes (M < 10) when sym=False, contradicting the documentation which states they should be equivalent.

## Property-Based Test

```python
@given(st.integers(min_value=2, max_value=10))
def test_tukey_hann_equivalence(M):
    """Test that Tukey(alpha=1) equals Hann as documented."""
    tukey = sig.windows.tukey(M, alpha=1.0, sym=False)
    hann = sig.windows.hann(M, sym=False)
    assert np.allclose(tukey, hann, rtol=1e-10, atol=1e-12)
```

**Failing input**: `M=2`

## Reproducing the Bug

```python
import scipy.signal as sig
import numpy as np

M = 2
tukey = sig.windows.tukey(M, alpha=1.0, sym=False)
hann = sig.windows.hann(M, sym=False)

print(f"Tukey(M={M}, alpha=1, sym=False): {tukey}")
print(f"Hann(M={M}, sym=False): {hann}")
print(f"Equal: {np.array_equal(tukey, hann)}")
```

## Why This Is A Bug

The documentation for `scipy.signal.windows.tukey` explicitly states: "If one, the Tukey window is equivalent to a Hann window." However, this equivalence does not hold for small window sizes (M < 10) when sym=False. The windows produce different values, violating the documented contract.

## Fix

The issue appears to be in the edge case handling for small windows in the Tukey implementation. Either the documentation should be updated to clarify this limitation, or the implementation should be fixed to ensure equivalence for all window sizes. The discrepancy only occurs with sym=False and small M values.

For M >= 10 with sym=False, or any M with sym=True (default), the equivalence holds correctly.