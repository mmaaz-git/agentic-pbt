import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import random
from hypothesis import given, strategies as st, settings, assume
import pytest
from tokenizers import Tokenizer, ByteLevelBPETokenizer, BertWordPieceTokenizer
from tokenizers.models import BPE, WordPiece
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.trainers import BpeTrainer, WordPieceTrainer


# Helper to create a trained tokenizer for testing
def create_trained_tokenizer(tokenizer_type="bpe"):
    """Create a tokenizer trained on sample data"""
    if tokenizer_type == "bpe":
        tokenizer = ByteLevelBPETokenizer()
        # Train on diverse text
        training_data = [
            "Hello world",
            "This is a test",
            "Testing tokenizers",
            "The quick brown fox jumps over the lazy dog",
            "1234567890",
            "Special characters: !@#$%^&*()",
            "Unicode: café, naïve, résumé",
            "Emojis: 😀 🎉 🚀",
            "Mixed case: HeLLo WoRLd",
            "Punctuation: Hello, world! How are you?",
            "Numbers and text: 42 is the answer",
        ]
        tokenizer.train_from_iterator(training_data, vocab_size=500, min_frequency=1)
    elif tokenizer_type == "bert":
        tokenizer = BertWordPieceTokenizer()
        training_data = [
            "Hello world",
            "This is a test",
            "Testing tokenizers",
            "The quick brown fox jumps over the lazy dog",
        ]
        tokenizer.train_from_iterator(training_data, vocab_size=100)
    else:
        tokenizer = Tokenizer(BPE())
        tokenizer.pre_tokenizer = Whitespace()
        trainer = BpeTrainer(vocab_size=100, min_frequency=1)
        tokenizer.train_from_iterator(["hello world", "test text"], trainer)
    
    return tokenizer


# Strategy for generating valid text inputs
text_strategy = st.text(min_size=0, max_size=100)
non_empty_text_strategy = st.text(min_size=1, max_size=100)


# Test 1: Round-trip property for encode/decode
@given(text=text_strategy)
@settings(max_examples=500)
def test_encode_decode_round_trip(text):
    """Test that decode(encode(x)) preserves the text"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Encode and decode
    encoding = tokenizer.encode(text)
    decoded = tokenizer.decode(encoding.ids)
    
    # The round-trip should preserve the text
    assert decoded == text, f"Round-trip failed: {repr(text)} -> {repr(decoded)}"


# Test 2: Batch encoding consistency
@given(texts=st.lists(text_strategy, min_size=1, max_size=10))
@settings(max_examples=200)
def test_batch_encoding_consistency(texts):
    """Test that batch encoding produces same results as individual encoding"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Encode individually
    individual_encodings = [tokenizer.encode(text) for text in texts]
    individual_ids = [enc.ids for enc in individual_encodings]
    
    # Encode as batch
    batch_encodings = tokenizer.encode_batch(texts)
    batch_ids = [enc.ids for enc in batch_encodings]
    
    # They should be the same
    assert batch_ids == individual_ids, "Batch encoding differs from individual encoding"


# Test 3: Token ID round-trip consistency
@given(text=non_empty_text_strategy)
@settings(max_examples=200)
def test_token_id_round_trip(text):
    """Test that token_to_id and id_to_token are inverse operations"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Get vocabulary
    vocab = tokenizer.get_vocab()
    
    # For each token in vocabulary, test round-trip
    for token, token_id in vocab.items():
        # id_to_token should return the token
        retrieved_token = tokenizer.id_to_token(token_id)
        assert retrieved_token == token, f"id_to_token({token_id}) returned {retrieved_token}, expected {token}"
        
        # token_to_id should return the id
        retrieved_id = tokenizer.token_to_id(token)
        assert retrieved_id == token_id, f"token_to_id({token}) returned {retrieved_id}, expected {token_id}"


# Test 4: Vocabulary size consistency
@given(add_tokens=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5))
@settings(max_examples=100)
def test_vocab_size_consistency(add_tokens):
    """Test that vocabulary size is consistent with and without added tokens"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Get initial vocab size
    size_with_added = tokenizer.get_vocab_size(with_added_tokens=True)
    size_without_added = tokenizer.get_vocab_size(with_added_tokens=False)
    
    # With added tokens should be >= without
    assert size_with_added >= size_without_added
    
    # Add tokens
    if add_tokens:
        # Filter out duplicates
        unique_tokens = list(set(add_tokens))
        num_added = tokenizer.add_tokens(unique_tokens)
        
        # New size should increase by number actually added
        new_size_with_added = tokenizer.get_vocab_size(with_added_tokens=True)
        assert new_size_with_added == size_with_added + num_added


# Test 5: Padding length invariant
@given(
    texts=st.lists(text_strategy, min_size=2, max_size=5),
    pad_length=st.integers(min_value=10, max_value=50)
)
@settings(max_examples=100)
def test_padding_length_invariant(texts, pad_length):
    """Test that padding produces consistent lengths"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Enable padding
    tokenizer.enable_padding(length=pad_length)
    
    # Encode texts
    encodings = tokenizer.encode_batch(texts)
    
    # All should have the same length
    lengths = [len(enc.ids) for enc in encodings]
    assert all(l == pad_length for l in lengths), f"Padding failed: got lengths {lengths}, expected all {pad_length}"


# Test 6: Truncation length invariant
@given(
    text=st.text(min_size=20, max_size=200),
    max_length=st.integers(min_value=5, max_value=20)
)
@settings(max_examples=100)
def test_truncation_length_invariant(text, max_length):
    """Test that truncation respects max_length"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Enable truncation
    tokenizer.enable_truncation(max_length=max_length)
    
    # Encode text
    encoding = tokenizer.encode(text)
    
    # Length should be <= max_length
    assert len(encoding.ids) <= max_length, f"Truncation failed: got length {len(encoding.ids)}, max was {max_length}"


# Test 7: Special tokens handling
@given(text=text_strategy)
@settings(max_examples=200)
def test_special_tokens_handling(text):
    """Test that special tokens are handled correctly in decode"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Add a special token
    special_token = "[SPECIAL]"
    tokenizer.add_special_tokens([special_token])
    special_id = tokenizer.token_to_id(special_token)
    
    # Create encoding with special token
    encoding = tokenizer.encode(text)
    ids_with_special = [special_id] + encoding.ids + [special_id]
    
    # Decode with skip_special_tokens=True
    decoded_skip = tokenizer.decode(ids_with_special, skip_special_tokens=True)
    
    # Decode with skip_special_tokens=False
    decoded_no_skip = tokenizer.decode(ids_with_special, skip_special_tokens=False)
    
    # When skipping, special tokens should not appear
    assert special_token not in decoded_skip
    # When not skipping, they should appear
    assert decoded_no_skip.startswith(special_token) and decoded_no_skip.endswith(special_token)


# Test 8: Empty input handling
def test_empty_input_handling():
    """Test that empty inputs are handled correctly"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Empty string should encode to empty
    encoding = tokenizer.encode("")
    assert encoding.ids == []
    assert encoding.tokens == []
    
    # Decode empty should return empty
    decoded = tokenizer.decode([])
    assert decoded == ""
    
    # Batch with empty should work
    batch = tokenizer.encode_batch(["", "hello", ""])
    assert batch[0].ids == []
    assert batch[2].ids == []


# Test 9: Unicode handling
@given(text=st.text(alphabet=st.characters(min_codepoint=0x0100, max_codepoint=0x10FF), min_size=1, max_size=50))
@settings(max_examples=100)
def test_unicode_handling(text):
    """Test that unicode text is handled correctly"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # Should not crash on unicode
    encoding = tokenizer.encode(text)
    decoded = tokenizer.decode(encoding.ids)
    
    # ByteLevelBPE preserves text exactly
    assert decoded == text


# Test 10: Null/None input validation
def test_none_input_validation():
    """Test that None inputs are properly rejected"""
    tokenizer = create_trained_tokenizer("bpe")
    
    # encode should reject None
    with pytest.raises(ValueError, match="can't be `None`"):
        tokenizer.encode(None)
    
    # decode should reject None
    with pytest.raises(ValueError, match="None input is not valid"):
        tokenizer.decode(None)
    
    # encode_batch should reject None
    with pytest.raises(ValueError, match="can't be `None`"):
        tokenizer.encode_batch(None)
    
    # decode_batch should reject None
    with pytest.raises(ValueError, match="None input is not valid"):
        tokenizer.decode_batch(None)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])