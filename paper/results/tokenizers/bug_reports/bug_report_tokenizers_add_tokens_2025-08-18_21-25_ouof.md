# Bug Report: tokenizers add_tokens() Returns Incorrect Count for Existing Tokens

**Target**: `tokenizers.ByteLevelBPETokenizer.add_tokens`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `add_tokens()` method returns 1 when adding an existing token but doesn't actually increase the vocabulary size, leading to inconsistent state.

## Property-Based Test

```python
@given(add_tokens=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5))
@settings(max_examples=100)
def test_vocab_size_consistency(add_tokens):
    """Test that vocabulary size is consistent with and without added tokens"""
    tokenizer = create_trained_tokenizer("bpe")
    
    size_with_added = tokenizer.get_vocab_size(with_added_tokens=True)
    size_without_added = tokenizer.get_vocab_size(with_added_tokens=False)
    
    assert size_with_added >= size_without_added
    
    if add_tokens:
        unique_tokens = list(set(add_tokens))
        num_added = tokenizer.add_tokens(unique_tokens)
        
        new_size_with_added = tokenizer.get_vocab_size(with_added_tokens=True)
        assert new_size_with_added == size_with_added + num_added
```

**Failing input**: `add_tokens=['0']`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')
from tokenizers import ByteLevelBPETokenizer

tokenizer = ByteLevelBPETokenizer()
tokenizer.train_from_iterator(
    ["Hello world", "1234567890"],
    vocab_size=500,
    min_frequency=1
)

initial_size = tokenizer.get_vocab_size()
num_added = tokenizer.add_tokens(['0'])
final_size = tokenizer.get_vocab_size()

print(f"Initial vocab size: {initial_size}")
print(f"Tokens reportedly added: {num_added}")
print(f"Final vocab size: {final_size}")
print(f"Expected final size: {initial_size + num_added}")
print(f"Bug: {final_size != initial_size + num_added}")
```

## Why This Is A Bug

The `add_tokens()` method returns the number of tokens it claims to have added. When it returns 1, the vocabulary size should increase by 1. However, when adding a token that already exists in the vocabulary, it returns 1 but doesn't actually increase the vocabulary size. This violates the contract that the return value represents the actual number of tokens added to the vocabulary.

## Fix

The method should check if a token already exists before claiming to add it:

```diff
def add_tokens(self, tokens):
    added_count = 0
    for token in tokens:
-       # Current behavior: always reports adding the token
-       self._internal_add_token(token)
-       added_count += 1
+       # Fixed behavior: only count if actually added
+       if token not in self.get_vocab():
+           self._internal_add_token(token)
+           added_count += 1
    return added_count
```