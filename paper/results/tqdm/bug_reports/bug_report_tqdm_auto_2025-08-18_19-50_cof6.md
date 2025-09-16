# Bug Report: tqdm.auto Negative Progress Allowed

**Target**: `tqdm.auto.tqdm`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

tqdm allows progress counter to become negative when update() is called with negative values, violating the fundamental invariant that progress should never be negative.

## Property-Based Test

```python
@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=100))
def test_update_with_negative_clamps_at_zero(updates):
    """Property: Progress should never go below 0"""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        t = tqdm(total=1000)
    
        for update_val in updates:
            t.update(update_val)
            assert t.n >= 0, f"Progress n={t.n} should never be negative"
    
        t.close()
    finally:
        sys.stderr = old_stderr
```

**Failing input**: `updates=[-1]`

## Reproducing the Bug

```python
from tqdm.auto import tqdm

t = tqdm(total=100)
print(f"Initial position: {t.n}")  # 0

t.update(-10)
print(f"After update(-10): {t.n}")  # -10

assert t.n >= 0, f"Progress should never be negative, but n={t.n}"
```

## Why This Is A Bug

Progress bars represent completion from 0% to 100%. Negative progress has no meaningful interpretation and breaks the fundamental contract of a progress bar. Users expect `n` to be clamped at 0 as the minimum value.

## Fix

The update method should clamp the new position to be non-negative:

```diff
def update(self, n=1):
    if self.disable:
        return
    if n:
        self.n += n
+       self.n = max(0, self.n)  # Ensure n never goes below 0
    
    # Rest of the update logic...
```