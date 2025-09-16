import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.decoders as decoders
from hypothesis import given, strategies as st, assume, settings
import re

# Strategy for valid tokens
token_strategy = st.text(min_size=1, max_size=50).filter(lambda s: s.strip() != "")

# Test 1: ByteFallback decoder - hex token conversion
@given(st.integers(min_value=0, max_value=255))
def test_bytefallback_hex_conversion(byte_val):
    """ByteFallback should convert <0xHH> tokens to corresponding bytes"""
    decoder = decoders.ByteFallback()
    hex_token = f"<0x{byte_val:02x}>"
    result = decoder.decode([hex_token])
    
    # The result should contain the corresponding character
    # For valid UTF-8 bytes, it should decode properly
    if byte_val < 128:  # ASCII range
        expected_char = chr(byte_val)
        assert expected_char in result, f"Expected '{expected_char}' in result for {hex_token}, got '{result}'"

# Test 2: ByteFallback with multiple hex tokens
@given(st.lists(st.integers(min_value=0, max_value=127), min_size=1, max_size=10))
def test_bytefallback_multiple_hex_tokens(byte_vals):
    """ByteFallback should handle multiple hex tokens correctly"""
    decoder = decoders.ByteFallback()
    hex_tokens = [f"<0x{b:02x}>" for b in byte_vals]
    result = decoder.decode(hex_tokens)
    
    # All ASCII characters should be in the result
    expected = ''.join(chr(b) for b in byte_vals)
    assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 3: Replace decoder - all occurrences replaced
@given(
    st.text(min_size=1, max_size=10).filter(lambda s: s != ""),
    st.text(min_size=1, max_size=10),
    st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10)
)
def test_replace_all_occurrences(pattern, replacement, base_tokens):
    """Replace decoder should replace all occurrences of pattern"""
    decoder = decoders.Replace(pattern, replacement)
    
    # Create tokens with the pattern
    tokens = [token + pattern + token for token in base_tokens]
    result = decoder.decode(tokens)
    
    # Pattern should not exist in result if it was in tokens
    if pattern in ''.join(tokens):
        assert pattern not in result or pattern == replacement, \
            f"Pattern '{pattern}' still in result: '{result}'"

# Test 4: Metaspace decoder - meta character replacement
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
def test_metaspace_replacement(tokens):
    """Metaspace should replace ▁ with spaces"""
    decoder = decoders.Metaspace()
    
    # Add meta character to tokens
    tokens_with_meta = [f"▁{token}" for token in tokens]
    result = decoder.decode(tokens_with_meta)
    
    # Check that ▁ is replaced with space
    assert "▁" not in result, f"Meta character still in result: '{result}'"
    # Should have spaces where meta characters were
    assert " " in result or len(tokens) == 0, f"No spaces found in result: '{result}'"

# Test 5: WordPiece decoder - prefix handling
@given(st.lists(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), 
                        min_size=1, max_size=10), min_size=2, max_size=10))
def test_wordpiece_prefix_removal(words):
    """WordPiece should handle ## prefix correctly"""
    decoder = decoders.WordPiece(prefix="##", cleanup=False)
    
    # First word normal, rest with prefix
    tokens = [words[0]] + [f"##{word}" for word in words[1:]]
    result = decoder.decode(tokens)
    
    # The ## prefix should be removed for continuation tokens
    assert "##" not in result, f"Prefix ## still in result: '{result}'"
    # Words should be concatenated
    expected_concat = ''.join(words)
    assert expected_concat in result.replace(" ", ""), \
        f"Expected concatenation '{expected_concat}' not found in '{result}'"

# Test 6: Strip decoder - character stripping
@given(
    st.lists(st.text(min_size=5, max_size=20), min_size=1, max_size=10),
    st.integers(min_value=1, max_value=3)
)
def test_strip_left_characters(tokens, n):
    """Strip decoder should remove n characters from left of each token"""
    decoder = decoders.Strip(left=n)
    
    # Filter tokens that are long enough
    valid_tokens = [t for t in tokens if len(t) > n]
    assume(len(valid_tokens) > 0)
    
    result = decoder.decode(valid_tokens)
    
    # Each token should have n characters stripped from left
    expected_parts = [t[n:] for t in valid_tokens]
    expected = ''.join(expected_parts)
    
    assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 7: Strip decoder - right stripping
@given(
    st.lists(st.text(min_size=5, max_size=20), min_size=1, max_size=10),
    st.integers(min_value=1, max_value=3)
)
def test_strip_right_characters(tokens, n):
    """Strip decoder should remove n characters from right of each token"""
    decoder = decoders.Strip(right=n)
    
    # Filter tokens that are long enough
    valid_tokens = [t for t in tokens if len(t) > n]
    assume(len(valid_tokens) > 0)
    
    result = decoder.decode(valid_tokens)
    
    # Each token should have n characters stripped from right
    expected_parts = [t[:-n] if len(t) > n else "" for t in valid_tokens]
    expected = ''.join(expected_parts)
    
    assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 8: Fuse decoder - concatenation property
@given(st.lists(token_strategy, min_size=1, max_size=10))
def test_fuse_concatenation(tokens):
    """Fuse decoder should concatenate all tokens into a single string"""
    decoder = decoders.Fuse()
    result = decoder.decode(tokens)
    
    # Result should be concatenation of all tokens
    expected = ''.join(tokens)
    assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 9: Sequence decoder - composition property
@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
def test_sequence_composition(tokens):
    """Sequence decoder should apply decoders in order"""
    # Create a sequence of Strip decoders
    decoder1 = decoders.Strip(left=1)
    decoder2 = decoders.Strip(right=1)
    seq_decoder = decoders.Sequence([decoder1, decoder2])
    
    # Filter tokens that are long enough for both strips
    valid_tokens = [t for t in tokens if len(t) > 2]
    assume(len(valid_tokens) > 0)
    
    result = seq_decoder.decode(valid_tokens)
    
    # Should be equivalent to applying both strips
    expected_parts = [t[1:-1] if len(t) > 2 else "" for t in valid_tokens]
    expected = ''.join(expected_parts)
    
    assert result == expected, f"Expected '{expected}', got '{result}'"

# Test 10: BPEDecoder - suffix handling
@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10))
def test_bpe_suffix_replacement(tokens):
    """BPEDecoder should replace suffix with whitespace"""
    suffix = "</w>"
    decoder = decoders.BPEDecoder(suffix=suffix)
    
    # Add suffix to some tokens
    tokens_with_suffix = []
    for i, token in enumerate(tokens):
        if i % 2 == 0:
            tokens_with_suffix.append(token + suffix)
        else:
            tokens_with_suffix.append(token)
    
    result = decoder.decode(tokens_with_suffix)
    
    # Suffix should be replaced with space
    assert suffix not in result, f"Suffix '{suffix}' still in result: '{result}'"

# Test 11: CTC decoder - pad token handling
@given(st.lists(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), 
                        min_size=1, max_size=5), min_size=1, max_size=10))
def test_ctc_pad_token_removal(tokens):
    """CTC decoder should handle pad tokens correctly"""
    pad_token = "<pad>"
    decoder = decoders.CTC(pad_token=pad_token, cleanup=False)
    
    # Insert pad tokens between some tokens
    tokens_with_pad = []
    for i, token in enumerate(tokens):
        tokens_with_pad.append(token)
        if i < len(tokens) - 1 and i % 2 == 0:
            tokens_with_pad.append(pad_token)
    
    result = decoder.decode(tokens_with_pad)
    
    # Pad token should not appear in result
    assert pad_token not in result, f"Pad token '{pad_token}' still in result: '{result}'"

if __name__ == "__main__":
    print("Running property-based tests for tokenizers.decoders...")
    print("=" * 60)