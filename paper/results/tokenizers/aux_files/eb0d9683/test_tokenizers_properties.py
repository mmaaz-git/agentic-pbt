#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from tokenizers import Tokenizer, tokenizers
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace
import string

# Create a pre-trained tokenizer for testing
def create_test_tokenizer():
    tokenizer = Tokenizer(BPE())
    tokenizer.pre_tokenizer = Whitespace()
    trainer = BpeTrainer(special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"])
    
    # Train on a reasonable corpus
    corpus = [
        "The quick brown fox jumps over the lazy dog",
        "Hello world this is a test",
        "Testing tokenizer properties with hypothesis",
        "abcdefghijklmnopqrstuvwxyz",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "0123456789",
        "!@#$%^&*()",
    ] * 5
    
    tokenizer.train_from_iterator(corpus, trainer)
    return tokenizer

# Global tokenizer instance
tokenizer = create_test_tokenizer()

# Strategy for generating reasonable text
text_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " .,!?'-",
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())  # Ensure non-empty after stripping

# Test 1: Round-trip property for single encoding
@given(text_strategy)
@settings(max_examples=100)
def test_encode_decode_roundtrip(text):
    """Test that encoding and decoding preserves the original text."""
    encoding = tokenizer.encode(text)
    decoded = tokenizer.decode(encoding.ids)
    
    # The decoded text should match the original
    # Note: Some tokenizers may normalize whitespace
    assert decoded.strip() == text.strip(), f"Round-trip failed: '{text}' -> '{decoded}'"

# Test 2: Batch operations consistency
@given(st.lists(text_strategy, min_size=1, max_size=10))
@settings(max_examples=100)
def test_batch_consistency(texts):
    """Test that batch operations are consistent with single operations."""
    # Encode individually
    individual_encodings = [tokenizer.encode(text) for text in texts]
    individual_ids = [enc.ids for enc in individual_encodings]
    
    # Encode as batch
    batch_encodings = tokenizer.encode_batch(texts)
    batch_ids = [enc.ids for enc in batch_encodings]
    
    # The IDs should match
    assert individual_ids == batch_ids, "Batch encoding differs from individual encoding"
    
    # Test decode consistency
    individual_decoded = [tokenizer.decode(ids) for ids in individual_ids]
    batch_decoded = tokenizer.decode_batch(batch_ids)
    
    # Check if batch decode matches individual decode
    for i, (ind, batch) in enumerate(zip(individual_decoded, batch_decoded)):
        assert ind == batch, f"Batch decode differs at index {i}: '{ind}' vs '{batch}'"

# Test 3: Encoding mapping consistency
@given(text_strategy)
@settings(max_examples=100)
def test_encoding_mapping_consistency(text):
    """Test that char_to_token and token_to_chars mappings are consistent."""
    encoding = tokenizer.encode(text)
    
    # For each token, check that its character span maps back correctly
    for token_idx in range(len(encoding.tokens)):
        char_span = encoding.token_to_chars(token_idx)
        if char_span is not None:
            start, end = char_span
            
            # Check that characters in this span map back to this token
            for char_idx in range(start, end):
                mapped_token = encoding.char_to_token(char_idx)
                assert mapped_token == token_idx, \
                    f"Inconsistent mapping: char {char_idx} -> token {mapped_token}, expected {token_idx}"
            
            # Verify the token text matches the character span
            token_text = text[start:end]
            assert token_text == encoding.tokens[token_idx], \
                f"Token text mismatch: '{token_text}' vs '{encoding.tokens[token_idx]}'"

# Test 4: Offsets consistency
@given(text_strategy)
@settings(max_examples=100)
def test_offsets_consistency(text):
    """Test that offsets correctly represent token positions in the original text."""
    encoding = tokenizer.encode(text)
    
    for i, (start, end) in enumerate(encoding.offsets):
        # Extract text using offsets
        token_from_offset = text[start:end]
        
        # Compare with the actual token
        assert token_from_offset == encoding.tokens[i], \
            f"Offset mismatch for token {i}: '{token_from_offset}' vs '{encoding.tokens[i]}'"

# Test 5: NormalizedString transformations
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_normalized_string_lowercase_idempotence(text):
    """Test that lowercase transformation is idempotent."""
    norm1 = tokenizers.NormalizedString(text)
    norm1.lowercase()
    first_result = str(norm1)
    
    norm2 = tokenizers.NormalizedString(first_result)
    norm2.lowercase()
    second_result = str(norm2)
    
    # Lowercase should be idempotent
    assert first_result == second_result, \
        f"Lowercase not idempotent: '{first_result}' -> '{second_result}'"

@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_normalized_string_strip_idempotence(text):
    """Test that strip transformation is idempotent."""
    norm1 = tokenizers.NormalizedString(text)
    norm1.strip()
    first_result = str(norm1)
    
    norm2 = tokenizers.NormalizedString(first_result)
    norm2.strip()
    second_result = str(norm2)
    
    # Strip should be idempotent
    assert first_result == second_result, \
        f"Strip not idempotent: '{first_result}' -> '{second_result}'"

# Test 6: AddedToken properties
@given(
    content=st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
    single_word=st.booleans(),
    lstrip=st.booleans(),
    rstrip=st.booleans(),
    normalized=st.booleans(),
    special=st.booleans()
)
@settings(max_examples=50)
def test_added_token_creation(content, single_word, lstrip, rstrip, normalized, special):
    """Test that AddedToken can be created with various parameters."""
    token = tokenizers.AddedToken(
        content=content,
        single_word=single_word,
        lstrip=lstrip,
        rstrip=rstrip,
        normalized=normalized,
        special=special
    )
    
    # Token should be created successfully and have the correct content
    assert str(token) == content, f"AddedToken content mismatch: '{token}' vs '{content}'"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])