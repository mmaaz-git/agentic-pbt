# Bug Report: tokenizers.Tokenizer Silently Drops Unknown Characters

**Target**: `tokenizers.Tokenizer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Tokenizer silently drops characters that are not in its vocabulary instead of using the [UNK] token, causing encode/decode round-trip failures.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Create tokenizer with limited vocabulary
tokenizer = Tokenizer(BPE())
tokenizer.pre_tokenizer = Whitespace()
trainer = BpeTrainer(special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"])
corpus = ["The quick brown fox", "Hello world", "abc", "123", "!@#"] * 5
tokenizer.train_from_iterator(corpus, trainer)

@given(st.text(min_size=1, max_size=100))
def test_encode_decode_roundtrip(text):
    encoding = tokenizer.encode(text)
    decoded = tokenizer.decode(encoding.ids)
    assert decoded.strip() == text.strip()
```

**Failing input**: `'?'`

## Reproducing the Bug

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

tokenizer = Tokenizer(BPE())
tokenizer.pre_tokenizer = Whitespace()
trainer = BpeTrainer(special_tokens=["[UNK]"])
corpus = ["abc", "123", "!@#"] * 5
tokenizer.train_from_iterator(corpus, trainer)

text = "?"
encoding = tokenizer.encode(text)
decoded = tokenizer.decode(encoding.ids)

print(f"Original: '{text}'")
print(f"Tokens: {encoding.tokens}")  # []
print(f"Decoded: '{decoded}'")        # ''
print(f"Match: {decoded == text}")    # False
```

## Why This Is A Bug

The tokenizer includes an [UNK] token in its special tokens but doesn't use it when encountering unknown characters. Instead, it silently drops them, violating the fundamental expectation that tokenization should be reversible or at least preserve information through the [UNK] token.

## Fix

The tokenizer should map unknown characters to the [UNK] token instead of dropping them. This would require modifying the BPE model's handling of out-of-vocabulary characters to properly utilize the special [UNK] token when configured.