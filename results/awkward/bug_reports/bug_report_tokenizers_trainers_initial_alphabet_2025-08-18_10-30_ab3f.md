# Bug Report: tokenizers.trainers BpeTrainer and WordPieceTrainer initial_alphabet Order Not Preserved

**Target**: `tokenizers.trainers.BpeTrainer` and `tokenizers.trainers.WordPieceTrainer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

BpeTrainer and WordPieceTrainer do not preserve the order of characters in the `initial_alphabet` parameter, violating expected behavior and potentially affecting tokenization consistency.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tokenizers.trainers as trainers

@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=20))
def test_bpe_trainer_initial_alphabet_preserves_order(strings):
    trainer = trainers.BpeTrainer(initial_alphabet=strings)
    expected = [s[0] for s in strings]
    
    actual = trainer.initial_alphabet
    
    unique_expected = []
    seen = set()
    for char in expected:
        if char not in seen:
            unique_expected.append(char)
            seen.add(char)
    
    actual_positions = {}
    for i, char in enumerate(actual):
        if char not in actual_positions:
            actual_positions[char] = i
    
    for i in range(len(unique_expected) - 1):
        char1 = unique_expected[i]
        char2 = unique_expected[i + 1]
        if char1 in actual_positions and char2 in actual_positions:
            assert actual_positions[char1] < actual_positions[char2], \
                f"Order violated: '{char1}' should come before '{char2}'"
```

**Failing input**: `['0', '1']` produces `['1', '0']` instead of `['0', '1']`

## Reproducing the Bug

```python
import tokenizers.trainers as trainers

trainer = trainers.BpeTrainer(initial_alphabet=['0', '1'])
print(f"Input: ['0', '1']")
print(f"Output: {trainer.initial_alphabet}")

trainer = trainers.BpeTrainer(initial_alphabet=['a', 'b', 'c'])
print(f"Input: ['a', 'b', 'c']") 
print(f"Output: {trainer.initial_alphabet}")

trainer = trainers.WordPieceTrainer(initial_alphabet=['0', '1'])
print(f"Input: ['0', '1']")
print(f"Output: {trainer.initial_alphabet}")
```

## Why This Is A Bug

The documentation states that when strings in `initial_alphabet` contain more than one character, only the first character is kept. However, it doesn't mention that the order would be changed. Users expect the order to be preserved as this affects:
1. Tokenization consistency across different configurations
2. Reproducibility when using the same initial alphabet
3. Predictable behavior when defining character precedence

## Fix

The issue appears to be in the underlying Rust implementation that processes the initial_alphabet. The fix would require:
1. Preserving insertion order when processing initial_alphabet characters
2. Using an order-preserving data structure or explicitly maintaining the order
3. Ensuring both BpeTrainer and WordPieceTrainer behave consistently

Since this is a Rust library with Python bindings, the fix needs to be applied in the Rust codebase.