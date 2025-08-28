# Bug Report: tokenizers enable_padding() Doesn't Enforce Fixed Length

**Target**: `tokenizers.ByteLevelBPETokenizer.enable_padding`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

When `enable_padding(length=N)` is called, sequences longer than N are not truncated, violating the expectation that all outputs will have exactly length N.

## Property-Based Test

```python
@given(
    texts=st.lists(text_strategy, min_size=2, max_size=5),
    pad_length=st.integers(min_value=10, max_value=50)
)
@settings(max_examples=100)
def test_padding_length_invariant(texts, pad_length):
    """Test that padding produces consistent lengths"""
    tokenizer = create_trained_tokenizer("bpe")
    
    tokenizer.enable_padding(length=pad_length)
    
    encodings = tokenizer.encode_batch(texts)
    
    lengths = [len(enc.ids) for enc in encodings]
    assert all(l == pad_length for l in lengths), f"Padding failed: got lengths {lengths}, expected all {pad_length}"
```

**Failing input**: `texts=['', '000\x80\x80𐀀'], pad_length=10`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')
from tokenizers import ByteLevelBPETokenizer

tokenizer = ByteLevelBPETokenizer()
tokenizer.train_from_iterator(
    ["Hello world", "Testing", "1234567890"],
    vocab_size=500,
    min_frequency=1
)

tokenizer.enable_padding(length=10)

texts = ['', '000\x80\x80𐀀']
encodings = tokenizer.encode_batch(texts)

for text, enc in zip(texts, encodings):
    print(f"Text: {repr(text)}")
    print(f"Length: {len(enc.ids)} (expected 10)")

lengths = [len(enc.ids) for enc in encodings]
print(f"\nActual lengths: {lengths}")
print(f"Expected: [10, 10]")
print(f"Bug: Padding doesn't enforce fixed length")
```

## Why This Is A Bug

The `enable_padding()` method documentation states it sets "the length at which to pad", implying a fixed target length. Users reasonably expect that when they specify `length=10`, all outputs will have exactly 10 tokens - padding shorter sequences and truncating longer ones. However, the current implementation only pads shorter sequences but doesn't truncate longer ones, leading to inconsistent output lengths.

## Fix

The implementation should either:
1. Automatically enable truncation when a fixed padding length is specified:

```diff
def enable_padding(self, length=None, ...):
    if length is not None:
+       # When fixed length is specified, also enable truncation
+       self.enable_truncation(max_length=length)
    self._set_padding_params(length, ...)
```

2. Or clearly document that truncation must be enabled separately and raise a warning when sequences exceed the padding length.