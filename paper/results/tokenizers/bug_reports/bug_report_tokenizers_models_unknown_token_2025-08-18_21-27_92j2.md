# Bug Report: tokenizers.models Unknown Tokens Return None Instead of UNK ID

**Target**: `tokenizers.models.WordLevel`, `tokenizers.models.WordPiece`  
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

WordLevel and WordPiece models return `None` for unknown tokens instead of returning the ID of the configured unknown token, violating the documented behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import tokenizers.models

@given(
    vocab=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.integers(min_value=0, max_value=10000),
        min_size=1
    ).map(lambda v: {**v, "[UNK]": len(v)}),
    unknown_token=st.text(min_size=1, max_size=50)
)
def test_unknown_token_handling(vocab, unknown_token):
    assume(unknown_token not in vocab)
    
    model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")
    unk_id = vocab["[UNK]"]
    
    token_id = model.token_to_id(unknown_token)
    assert token_id == unk_id
```

**Failing input**: `vocab={'known': 0, '[UNK]': 1}, unknown_token='unknown'`

## Reproducing the Bug

```python
import tokenizers.models

vocab = {'known': 0, '[UNK]': 1}
model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")

unknown_token = "unknown"
result = model.token_to_id(unknown_token)

print(f"token_to_id('{unknown_token}'): {result}")
print(f"Expected: 1 (the ID of '[UNK]')")

assert result == 1  # AssertionError: None != 1
```

## Why This Is A Bug

According to the documentation, models configured with an `unk_token` should map unknown tokens to the ID of that unknown token. Returning `None` instead breaks this contract and can cause downstream failures in code expecting a valid integer ID for all inputs.

## Fix

The `token_to_id` method should check if the token exists in the vocabulary and return the UNK token's ID if not:

```diff
def token_to_id(self, token):
    if token in self.vocab:
        return self.vocab[token]
-   return None
+   elif self.unk_token and self.unk_token in self.vocab:
+       return self.vocab[self.unk_token]
+   else:
+       return None
```