# Bug Report: tokenizers.models.WordLevel Accepts Duplicate Token IDs Breaking Round-Trip Property

**Target**: `tokenizers.models.WordLevel`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

WordLevel model accepts vocabularies where multiple tokens map to the same ID, violating the bijection property between tokens and IDs and breaking round-trip guarantees.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tokenizers.models

@given(st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.integers(min_value=0, max_value=10000),
    min_size=1
).map(lambda v: {**v, "[UNK]": len(v)}))
def test_wordlevel_token_id_roundtrip(vocab):
    model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")
    
    for token in vocab:
        token_id = model.token_to_id(token)
        recovered_token = model.id_to_token(token_id)
        assert recovered_token == token
```

**Failing input**: `vocab={'0': 0, '1': 0, '[UNK]': 2}`

## Reproducing the Bug

```python
import tokenizers.models

vocab = {'0': 0, '1': 0, '[UNK]': 2}
model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")

token = '1'
token_id = model.token_to_id(token)  # Returns 0
recovered = model.id_to_token(token_id)  # Returns '0', not '1'

print(f"Round-trip for '1': '{token}' -> {token_id} -> '{recovered}'")
assert recovered == token  # AssertionError: '0' != '1'
```

## Why This Is A Bug

Tokenizers should maintain a bijection between vocabulary tokens and their IDs. When multiple tokens map to the same ID, `id_to_token()` can only return one token, making it impossible to correctly recover all original tokens. This violates the fundamental contract that `id_to_token(token_to_id(t)) == t` for all tokens in the vocabulary.

## Fix

The WordLevel constructor should validate that all token IDs in the vocabulary are unique and raise a ValueError if duplicates are detected:

```diff
class WordLevel:
    def __init__(self, vocab, unk_token):
+       # Validate that all IDs are unique
+       id_counts = {}
+       for token, token_id in vocab.items():
+           if token_id in id_counts:
+               raise ValueError(f"Duplicate ID {token_id} for tokens '{id_counts[token_id]}' and '{token}'")
+           id_counts[token_id] = token
        self.vocab = vocab
        self.unk_token = unk_token
```