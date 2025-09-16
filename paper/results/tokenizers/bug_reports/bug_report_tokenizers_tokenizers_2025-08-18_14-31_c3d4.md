# Bug Report: tokenizers.Encoding Incorrect Offsets When Unknown Characters Are Dropped

**Target**: `tokenizers.Encoding`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When the tokenizer drops unknown characters, the offsets in the Encoding object incorrectly point to the positions of the dropped characters instead of the actual token positions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

tokenizer = Tokenizer(BPE())
tokenizer.pre_tokenizer = Whitespace()
trainer = BpeTrainer(special_tokens=["[UNK]"])
corpus = ["abc", "123", "!"] * 5
tokenizer.train_from_iterator(corpus, trainer)

@given(st.text(min_size=1, max_size=100))
def test_offsets_consistency(text):
    encoding = tokenizer.encode(text)
    for i, (start, end) in enumerate(encoding.offsets):
        token_from_offset = text[start:end]
        assert token_from_offset == encoding.tokens[i]
```

**Failing input**: `'?!'`

## Reproducing the Bug

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

tokenizer = Tokenizer(BPE())
tokenizer.pre_tokenizer = Whitespace()
trainer = BpeTrainer(special_tokens=["[UNK]"])
corpus = ["!", "a", "b"] * 5
tokenizer.train_from_iterator(corpus, trainer)

text = "?!"
encoding = tokenizer.encode(text)

print(f"Text: '{text}'")
print(f"Tokens: {encoding.tokens}")    # ['!']
print(f"Offsets: {encoding.offsets}")  # [(0, 1)]

token = encoding.tokens[0]              # '!'
start, end = encoding.offsets[0]        # (0, 1)
substring = text[start:end]             # '?'

print(f"Token: '{token}'")
print(f"Substring at offset: '{substring}'")
print(f"Match: {token == substring}")   # False
```

## Why This Is A Bug

The offset (0, 1) points to the first character '?' in the text, but the actual token is '!' which is at position (1, 2). This breaks the fundamental contract that offsets should indicate where each token appears in the original text. This would cause issues for any application that relies on offsets for highlighting, alignment, or substring extraction.

## Fix

When dropping unknown characters during tokenization, the tokenizer should adjust the offsets to point to the actual positions of the retained tokens. The offset calculation logic needs to account for skipped characters and maintain correct alignment between tokens and their source positions.