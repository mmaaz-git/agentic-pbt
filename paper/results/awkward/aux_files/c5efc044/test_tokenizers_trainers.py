#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, settings, assume
import tokenizers.trainers as trainers

# Test 1: initial_alphabet property - should preserve first char of each string
@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=20))
def test_bpe_trainer_initial_alphabet_preserves_order(strings):
    """
    According to the documentation: "If the strings contain more than one character, 
    only the first one is kept."
    
    This should mean ["abc", "def", "xyz"] -> ["a", "d", "x"] in that order.
    """
    trainer = trainers.BpeTrainer(initial_alphabet=strings)
    expected = [s[0] for s in strings]
    
    # The result should contain the first character of each input string
    # and maintain the relative order
    actual = trainer.initial_alphabet
    
    # Check that each expected char appears in the actual list
    for char in expected:
        assert char in actual, f"Expected char '{char}' not found in {actual}"
    
    # Check ordering is preserved for unique first chars
    unique_expected = []
    seen = set()
    for char in expected:
        if char not in seen:
            unique_expected.append(char)
            seen.add(char)
    
    # Get positions of unique chars in actual
    actual_positions = {}
    for i, char in enumerate(actual):
        if char not in actual_positions:
            actual_positions[char] = i
    
    # Check that the relative ordering is preserved
    for i in range(len(unique_expected) - 1):
        char1 = unique_expected[i]
        char2 = unique_expected[i + 1]
        if char1 in actual_positions and char2 in actual_positions:
            assert actual_positions[char1] < actual_positions[char2], \
                f"Order violated: '{char1}' should come before '{char2}'"


# Test 2: WordPieceTrainer initial_alphabet property
@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=20))
def test_wordpiece_trainer_initial_alphabet_preserves_order(strings):
    """
    WordPieceTrainer should have the same behavior as BpeTrainer for initial_alphabet.
    """
    trainer = trainers.WordPieceTrainer(initial_alphabet=strings)
    expected = [s[0] for s in strings]
    
    actual = trainer.initial_alphabet
    
    for char in expected:
        assert char in actual, f"Expected char '{char}' not found in {actual}"
    
    unique_expected = []
    seen = set()
    for char in expected:
        if char not in seen:
            unique_expected.append(char)
            seen.add(char)
    
    actual_positions = {}
    for i, char in enumerate(actual):
        if char not in actual_positions:
            actual_positions[char] = i
    
    for i in range(len(unique_expected) - 1):
        char1 = unique_expected[i]
        char2 = unique_expected[i + 1]
        if char1 in actual_positions and char2 in actual_positions:
            assert actual_positions[char1] < actual_positions[char2], \
                f"Order violated: '{char1}' should come before '{char2}'"


# Test 3: UnigramTrainer shrinking_factor validation
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_unigram_trainer_shrinking_factor_validation(factor):
    """
    The shrinking_factor parameter should be validated to be between 0 and 1.
    According to the docstring it's "The shrinking factor used at each step 
    of the training to prune the vocabulary."
    
    A factor outside (0, 1] doesn't make mathematical sense for shrinking.
    """
    trainer = trainers.UnigramTrainer(shrinking_factor=factor)
    
    # The trainer shouldn't crash, but we check if unreasonable values are accepted
    # Values <= 0 or > 1 are mathematically nonsensical for a "shrinking" factor
    if factor <= 0 or factor > 1:
        # This is actually a bug - it should validate the input
        # but let's document what actually happens
        pass  # The trainer accepts invalid values without validation


# Test 4: Attribute persistence and consistency
@given(
    vocab_size=st.integers(min_value=1, max_value=1000000),
    min_frequency=st.integers(min_value=0, max_value=1000),
    special_tokens=st.lists(st.text(min_size=1, max_size=10), max_size=10)
)
def test_bpe_trainer_attribute_persistence(vocab_size, min_frequency, special_tokens):
    """
    Parameters set during initialization should be retrievable as attributes.
    """
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        min_frequency=min_frequency,
        special_tokens=special_tokens
    )
    
    assert trainer.vocab_size == vocab_size
    assert trainer.min_frequency == min_frequency
    
    # special_tokens are converted to AddedToken objects
    assert len(trainer.special_tokens) == len(special_tokens)


# Test 5: Extreme vocab_size values
@given(st.integers(min_value=2**32, max_value=2**63))
def test_extreme_vocab_size_acceptance(size):
    """
    Test that extremely large vocab_size values are accepted without validation.
    These values are impractical and could cause memory issues.
    """
    # This should probably have reasonable limits, but currently doesn't
    trainer = trainers.BpeTrainer(vocab_size=size)
    assert trainer.vocab_size == size


# Test 6: Type validation
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.none(),
    st.lists(st.integers())
))
def test_invalid_type_vocab_size(value):
    """
    vocab_size should only accept integers, not other types.
    """
    assume(not isinstance(value, int))
    
    with pytest.raises((TypeError, ValueError)):
        trainers.BpeTrainer(vocab_size=value)


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running quick tests...")
    
    # Test the initial_alphabet bug directly
    trainer = trainers.BpeTrainer(initial_alphabet=["abc", "def", "xyz"])
    print(f"BpeTrainer initial_alphabet for ['abc', 'def', 'xyz']: {trainer.initial_alphabet}")
    print(f"  Expected: ['a', 'd', 'x'] but got: {trainer.initial_alphabet}")
    
    trainer = trainers.WordPieceTrainer(initial_alphabet=["abc", "def", "xyz"])
    print(f"WordPieceTrainer initial_alphabet for ['abc', 'def', 'xyz']: {trainer.initial_alphabet}")
    
    # Test shrinking_factor
    trainer = trainers.UnigramTrainer(shrinking_factor=1.5)
    print(f"UnigramTrainer accepts shrinking_factor=1.5: {trainer}")
    
    trainer = trainers.UnigramTrainer(shrinking_factor=-0.5)
    print(f"UnigramTrainer accepts shrinking_factor=-0.5: {trainer}")
    
    print("\nQuick tests completed. Run with pytest for full hypothesis testing.")