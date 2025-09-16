# Bug Report: tokenizers.trainers UnigramTrainer Accepts Invalid shrinking_factor Values

**Target**: `tokenizers.trainers.UnigramTrainer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

UnigramTrainer accepts mathematically invalid values for the `shrinking_factor` parameter, including negative values and values greater than 1, which violate the semantic meaning of a "shrinking" factor.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tokenizers.trainers as trainers

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_unigram_trainer_shrinking_factor_validation(factor):
    if factor <= 0 or factor > 1:
        # Should raise ValueError for invalid shrinking factors
        with pytest.raises(ValueError):
            trainer = trainers.UnigramTrainer(shrinking_factor=factor)
    else:
        # Valid values should work
        trainer = trainers.UnigramTrainer(shrinking_factor=factor)
        assert trainer is not None
```

**Failing input**: Values like `-1.0`, `0.0`, `1.5`, `100.0` are all accepted without validation

## Reproducing the Bug

```python
import tokenizers.trainers as trainers

invalid_values = [-1.0, -0.5, 0.0, 1.5, 2.0, 100.0]

for value in invalid_values:
    trainer = trainers.UnigramTrainer(shrinking_factor=value)
    print(f"shrinking_factor={value} - ACCEPTED (should be rejected!)")
    print(f"  Trainer: {trainer}")
```

## Why This Is A Bug

The `shrinking_factor` parameter is documented as "The shrinking factor used at each step of the training to prune the vocabulary." A shrinking factor:
1. Must be positive (> 0) to have mathematical meaning
2. Must be ≤ 1 to actually shrink (not grow) the vocabulary
3. A value of 0 would eliminate the entire vocabulary
4. A value > 1 would grow the vocabulary instead of shrinking it
5. Negative values are mathematically nonsensical

Accepting invalid values could lead to:
- Unexpected training behavior
- Silent failures during tokenizer training
- Non-convergent or incorrect vocabulary pruning

## Fix

Add input validation in the UnigramTrainer constructor:

```diff
def __init__(self, shrinking_factor=0.75, ...):
+    if shrinking_factor <= 0 or shrinking_factor > 1:
+        raise ValueError(f"shrinking_factor must be in range (0, 1], got {shrinking_factor}")
    self.shrinking_factor = shrinking_factor
```

The validation should be implemented in the Rust layer where the actual UnigramTrainer is constructed.