# Bug Report: tokenizers.decoders.Strip Does Not Strip Characters

**Target**: `tokenizers.decoders.Strip`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The Strip decoder in tokenizers.decoders claims to strip n characters from the left or right of each token, but it doesn't strip any characters at all - it just concatenates the tokens unchanged.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tokenizers.decoders as decoders

@given(
    st.lists(st.text(min_size=5, max_size=20), min_size=1, max_size=10),
    st.integers(min_value=1, max_value=3)
)
def test_strip_left_characters(tokens, n):
    """Strip decoder should remove n characters from left of each token"""
    decoder = decoders.Strip(left=n)
    valid_tokens = [t for t in tokens if len(t) > n]
    if not valid_tokens:
        return
    
    result = decoder.decode(valid_tokens)
    expected_parts = [t[n:] for t in valid_tokens]
    expected = ''.join(expected_parts)
    
    assert result == expected, f"Expected '{expected}', got '{result}'"
```

**Failing input**: `tokens=['00000'], n=1`

## Reproducing the Bug

```python
import tokenizers.decoders as decoders

strip_decoder = decoders.Strip(left=2, right=1)
tokens = ["hello", "world"]
result = strip_decoder.decode(tokens)

print(f"Input: {tokens}")
print(f"Expected: 'lloor'")
print(f"Actual: '{result}'")
```

## Why This Is A Bug

The Strip decoder's docstring explicitly states: "Strips n left characters of each token, or n right characters of each token". The constructor accepts integer parameters for `left` and `right` to specify how many characters to strip. However, the decode() method completely ignores these parameters and returns the concatenated tokens without any stripping. This violates the documented contract.

## Fix

The decode() method needs to be implemented to actually strip the specified number of characters from each token before concatenation. The current implementation appears to be a no-op that just joins tokens.

```diff
class Strip(Decoder):
    def decode(self, tokens):
-       return ''.join(tokens)
+       stripped = []
+       for token in tokens:
+           start = self.left if hasattr(self, 'left') else 0
+           end = -self.right if hasattr(self, 'right') and self.right > 0 else None
+           if len(token) > start + (self.right if hasattr(self, 'right') else 0):
+               stripped.append(token[start:end])
+       return ''.join(stripped)
```