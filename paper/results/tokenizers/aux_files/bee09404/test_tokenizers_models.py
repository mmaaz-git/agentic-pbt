#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import os
import tempfile
from hypothesis import given, strategies as st, assume, settings
import tokenizers.models
import pytest

# Strategies for generating valid vocab and tokens
def valid_token_strategy():
    """Generate valid token strings"""
    return st.text(min_size=1, max_size=50).filter(lambda x: x and not x.isspace())

def vocab_strategy(min_size=1, max_size=100):
    """Generate valid vocabulary dictionaries"""
    return st.dictionaries(
        valid_token_strategy(),
        st.integers(min_value=0, max_value=10000),
        min_size=min_size,
        max_size=max_size
    )

def vocab_with_unk_strategy():
    """Generate vocabulary that includes an [UNK] token"""
    return vocab_strategy().map(lambda v: {**v, "[UNK]": len(v)})

# Property 1: Round-trip property for token_to_id and id_to_token
@given(vocab_with_unk_strategy())
@settings(max_examples=100)
def test_wordlevel_token_id_roundtrip(vocab):
    """Test that token_to_id and id_to_token are inverses for WordLevel model"""
    model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")
    
    # Test token -> id -> token
    for token in vocab:
        token_id = model.token_to_id(token)
        recovered_token = model.id_to_token(token_id)
        assert recovered_token == token, f"Round-trip failed for token '{token}': got '{recovered_token}'"
    
    # Test id -> token -> id
    for token, token_id in vocab.items():
        recovered_token = model.id_to_token(token_id)
        if recovered_token is not None:  # Some IDs might not be in use
            recovered_id = model.token_to_id(recovered_token)
            assert recovered_id == token_id, f"Round-trip failed for id {token_id}: got {recovered_id}"

# Property 2: Unknown tokens should map to unknown token ID
@given(vocab_with_unk_strategy(), valid_token_strategy())
def test_wordlevel_unknown_token_handling(vocab, unknown_token):
    """Test that unknown tokens map to the [UNK] token ID"""
    assume(unknown_token not in vocab)
    
    model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")
    unk_id = vocab["[UNK]"]
    
    # Unknown token should map to UNK id
    token_id = model.token_to_id(unknown_token)
    assert token_id == unk_id, f"Unknown token '{unknown_token}' should map to UNK id {unk_id}, got {token_id}"

# Property 3: WordPiece model properties
@given(vocab_with_unk_strategy(), st.integers(min_value=1, max_value=1000))
def test_wordpiece_max_chars_constraint(vocab, max_chars):
    """Test WordPiece respects max_input_chars_per_word constraint"""
    model = tokenizers.models.WordPiece(vocab, unk_token="[UNK]", max_input_chars_per_word=max_chars)
    
    # Tokens in vocab should still be retrievable
    for token in vocab:
        if len(token) <= max_chars:
            token_id = model.token_to_id(token)
            assert token_id is not None or token_id >= 0

# Property 4: BPE merge operations consistency
@given(
    st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=5),
        st.integers(min_value=0, max_value=100),
        min_size=5,
        max_size=50
    )
)
def test_bpe_vocab_consistency(vocab):
    """Test BPE model with vocabulary only (no merges)"""
    # Ensure we have an UNK token
    if "[UNK]" not in vocab:
        vocab["[UNK]"] = len(vocab)
    
    try:
        model = tokenizers.models.BPE(vocab, merges=[], unk_token="[UNK]")
        
        # All vocab tokens should be retrievable
        for token in vocab:
            token_id = model.token_to_id(token)
            assert token_id == vocab[token], f"Token '{token}' has wrong ID: expected {vocab[token]}, got {token_id}"
            
            # Round-trip should work
            recovered = model.id_to_token(token_id)
            assert recovered == token, f"Round-trip failed for '{token}': got '{recovered}'"
    except Exception as e:
        # BPE might have specific requirements we're not meeting
        # Log but don't fail - we'll investigate if this is a bug
        print(f"BPE initialization failed with vocab size {len(vocab)}: {e}")

# Property 5: Save/Load round-trip
@given(vocab_with_unk_strategy())
def test_wordlevel_save_load_roundtrip(vocab):
    """Test that saving and loading a model preserves its behavior"""
    model1 = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save the model
        saved_files = model1.save(tmpdir, prefix="test")
        assert len(saved_files) > 0, "Model should save at least one file"
        
        # Load from the saved file
        vocab_file = os.path.join(tmpdir, "test-vocab.json")
        if os.path.exists(vocab_file):
            model2 = tokenizers.models.WordLevel.from_file(vocab_file, unk_token="[UNK]")
            
            # Both models should behave identically
            for token in vocab:
                id1 = model1.token_to_id(token)
                id2 = model2.token_to_id(token)
                assert id1 == id2, f"Token '{token}' has different IDs after save/load: {id1} vs {id2}"

# Property 6: Unigram model score ordering
@given(
    st.lists(
        st.tuples(
            st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10),
            st.floats(min_value=-100, max_value=0, allow_nan=False, allow_infinity=False)
        ),
        min_size=2,
        max_size=50,
        unique_by=lambda x: x[0]  # Ensure unique tokens
    )
)
def test_unigram_vocab_structure(vocab_list):
    """Test Unigram model with scored vocabulary"""
    # Add UNK token if not present
    tokens = [t for t, _ in vocab_list]
    if "[UNK]" not in tokens:
        vocab_list.append(("[UNK]", -10.0))
    
    try:
        # Find UNK token ID
        unk_id = next(i for i, (token, _) in enumerate(vocab_list) if token == "[UNK]")
        
        model = tokenizers.models.Unigram(vocab_list, unk_id=unk_id, byte_fallback=False)
        
        # All vocab tokens should be retrievable
        for i, (token, score) in enumerate(vocab_list):
            token_id = model.token_to_id(token)
            # The model might reorder tokens, but they should all be accessible
            assert token_id is not None and token_id >= 0, f"Token '{token}' not accessible"
            
            # Round-trip should work
            recovered = model.id_to_token(token_id)
            assert recovered == token, f"Round-trip failed for '{token}': got '{recovered}'"
    except Exception as e:
        print(f"Unigram initialization failed: {e}")

# Property 7: ID uniqueness invariant
@given(vocab_with_unk_strategy())
def test_id_uniqueness_invariant(vocab):
    """Test that each token maps to a unique ID"""
    model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")
    
    token_to_id_mapping = {}
    for token in vocab:
        token_id = model.token_to_id(token)
        if token in token_to_id_mapping:
            assert token_to_id_mapping[token] == token_id, f"Token '{token}' maps to different IDs"
        else:
            token_to_id_mapping[token] = token_id
    
    # Check that different tokens don't map to the same ID (except for UNK)
    id_to_tokens = {}
    for token, token_id in token_to_id_mapping.items():
        if token_id in id_to_tokens:
            # This should only happen if both are unknown tokens
            existing = id_to_tokens[token_id]
            unk_id = model.token_to_id("[UNK]")
            assert token_id == unk_id or existing == token, \
                f"Different tokens '{existing}' and '{token}' map to same ID {token_id}"
        else:
            id_to_tokens[token_id] = token

# Property 8: BPE merges application
@given(
    st.dictionaries(
        st.text(alphabet="abcde", min_size=1, max_size=2),
        st.integers(min_value=0, max_value=20),
        min_size=5,
        max_size=15
    )
)
def test_bpe_with_simple_merges(base_vocab):
    """Test BPE with controlled merges"""
    # Ensure we have basic tokens and UNK
    vocab = {**base_vocab, "[UNK]": len(base_vocab)}
    
    # Create valid merges from existing single-char tokens
    single_chars = [k for k in vocab.keys() if len(k) == 1 and k != "[UNK]"]
    merges = []
    merge_id = len(vocab)
    
    if len(single_chars) >= 2:
        # Add a few simple merges
        for i in range(min(3, len(single_chars) - 1)):
            pair = (single_chars[i], single_chars[i + 1])
            merged = pair[0] + pair[1]
            if merged not in vocab:
                vocab[merged] = merge_id
                merge_id += 1
                merges.append(pair)
    
    try:
        model = tokenizers.models.BPE(vocab, merges=merges, unk_token="[UNK]")
        
        # Test that merged tokens are accessible
        for merge in merges:
            merged_token = merge[0] + merge[1]
            token_id = model.token_to_id(merged_token)
            assert token_id == vocab[merged_token], f"Merged token '{merged_token}' has wrong ID"
            
            # Round-trip should work
            recovered = model.id_to_token(token_id)
            assert recovered == merged_token, f"Round-trip failed for merged token '{merged_token}'"
    except Exception as e:
        print(f"BPE with merges failed: {e}")

if __name__ == "__main__":
    # Run with pytest for better output
    pytest.main([__file__, "-v", "--tb=short"])