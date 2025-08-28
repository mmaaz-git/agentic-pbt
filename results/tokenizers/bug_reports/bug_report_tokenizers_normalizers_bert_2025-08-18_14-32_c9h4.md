# Bug Report: tokenizers.normalizers.BertNormalizer not idempotent with Chinese characters

**Target**: `tokenizers.normalizers.BertNormalizer`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

BertNormalizer violates idempotence when processing Chinese characters. It adds spaces around Chinese characters on each application, causing the output to differ when applied multiple times.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tokenizers.normalizers as norm

@given(st.text())
def test_bert_normalizer_idempotent(text):
    normalizer = norm.BertNormalizer()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice
```

**Failing input**: `'㐀'` (Chinese character U+3400)

## Reproducing the Bug

```python
import tokenizers.normalizers as norm

bert = norm.BertNormalizer()
text = "㐀"  # Chinese character

once = bert.normalize_str(text)
twice = bert.normalize_str(once)
thrice = bert.normalize_str(twice)

print(f"Original: '{text}'")
print(f"After 1st normalize: '{once}'")
print(f"After 2nd normalize: '{twice}'")
print(f"After 3rd normalize: '{thrice}'")

assert once == twice  # Fails - ' 㐀 ' != '  㐀  '
```

## Why This Is A Bug

Idempotence is a fundamental property for normalizers - applying the same normalization twice should produce the same result as applying it once. This property is critical for:

1. **Data consistency**: Text that has already been normalized should not change when processed again
2. **Pipeline reliability**: In multi-stage processing pipelines, accidentally normalizing twice shouldn't corrupt the data
3. **BERT model expectations**: The BertNormalizer is designed to prepare text for BERT models, and inconsistent normalization can affect model performance

The bug occurs because the normalizer adds spaces around Chinese characters, but when it encounters a Chinese character that already has spaces around it, it adds more spaces instead of recognizing that the text is already normalized.

## Fix

The BertNormalizer's `handle_chinese_chars` logic should check if spaces are already present around Chinese characters before adding new ones, ensuring idempotent behavior. The fix would involve modifying the Chinese character handling to:
1. Check if the character already has the expected spacing
2. Only add spaces if they're not already present
3. Avoid adding multiple consecutive spaces