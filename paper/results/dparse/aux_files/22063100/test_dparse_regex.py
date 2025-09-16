#!/usr/bin/env python3
"""Property-based tests for dparse.regex module."""

import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from dparse.regex import HASH_REGEX
from dparse.parser import Parser


# Test 1: Regex pattern behavior - testing if the pattern matches what we expect
@given(
    algo=st.sampled_from(['sha256', 'sha384', 'sha512', 'md5', 'sha1']),
    hash_value=st.text(alphabet='0123456789abcdefABCDEF', min_size=32, max_size=128),
    separator=st.sampled_from(['=', ' ', '|'])  # Testing all characters in [=| ]
)
def test_hash_regex_matches_expected_formats(algo, hash_value, separator):
    """Test that HASH_REGEX matches the expected hash formats."""
    hash_string = f"--hash{separator}{algo}:{hash_value}"
    match = re.search(HASH_REGEX, hash_string)
    
    # The regex should match when separator is '=', ' ', or '|'
    # because the pattern [=| ] matches any of these three characters
    assert match is not None, f"Failed to match: {hash_string}"
    assert match.group() == hash_string


# Test 2: Parse_hashes idempotence - parsing already cleaned line
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_.=/', min_size=1))
def test_parse_hashes_idempotence(clean_line):
    """Running parse_hashes on a line without hashes should be idempotent."""
    assume('--hash' not in clean_line)  # Ensure no hash specifications
    
    line1, hashes1 = Parser.parse_hashes(clean_line)
    line2, hashes2 = Parser.parse_hashes(line1)
    
    assert line1 == line2
    assert hashes1 == hashes2 == []


# Test 3: Multiple hash extraction
@given(
    base_line=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_.=/', min_size=1, max_size=50),
    num_hashes=st.integers(min_value=1, max_value=5),
    algos=st.lists(st.sampled_from(['sha256', 'sha384', 'sha512']), min_size=1, max_size=5),
    separators=st.lists(st.sampled_from(['=', ' ', '|']), min_size=1, max_size=5)
)
def test_multiple_hash_extraction(base_line, num_hashes, algos, separators):
    """Test that parse_hashes correctly extracts multiple hash specifications."""
    assume('--hash' not in base_line)
    
    # Build a line with multiple hashes
    hashes_to_add = []
    for i in range(min(num_hashes, len(algos), len(separators))):
        algo = algos[i % len(algos)]
        sep = separators[i % len(separators)]
        hash_val = 'a' * 64  # Simple valid hash
        hashes_to_add.append(f"--hash{sep}{algo}:{hash_val}")
    
    line_with_hashes = base_line + " " + " ".join(hashes_to_add)
    
    cleaned_line, extracted_hashes = Parser.parse_hashes(line_with_hashes)
    
    # All hash specifications should be extracted
    assert len(extracted_hashes) == len(hashes_to_add)
    # The cleaned line should not contain any hash specifications
    assert '--hash' not in cleaned_line
    # Verify all hashes were extracted
    for hash_spec in hashes_to_add:
        assert hash_spec in extracted_hashes


# Test 4: Regex character class bug - testing if '|' is intentional
@given(st.text(alphabet='0123456789abcdefABCDEF', min_size=32, max_size=64))
def test_pipe_separator_in_hash_regex(hash_value):
    """Test if pipe '|' separator works as might be unintended in [=| ] pattern."""
    # The pattern [=| ] matches '=', '|', or ' ' (space)
    # But pip uses --hash=algo:value or --hash algo:value, never --hash|algo:value
    
    pipe_hash = f"--hash|sha256:{hash_value}"
    match = re.search(HASH_REGEX, pipe_hash)
    
    # This will match because [=| ] includes '|'
    assert match is not None
    assert match.group() == pipe_hash
    
    # But this is likely a bug since pip doesn't use pipe separator


# Test 5: Hash regex with non-word characters
@given(
    prefix=st.text(alphabet='!@#$%^&*()[]{}', min_size=1, max_size=5),
    suffix=st.text(alphabet='!@#$%^&*()[]{}', min_size=1, max_size=5)
)
def test_hash_regex_word_boundary(prefix, suffix):
    """Test that HASH_REGEX only matches word characters in algo and hash."""
    # \w+ only matches word characters (letters, digits, underscore)
    
    # These should NOT match because of special characters
    invalid_hash1 = f"--hash=sha{prefix}256:abc123"
    invalid_hash2 = f"--hash=sha256:abc{suffix}123"
    
    match1 = re.search(HASH_REGEX, invalid_hash1)
    match2 = re.search(HASH_REGEX, invalid_hash2)
    
    # The matches will be partial - only the valid word character parts
    if match1:
        assert match1.group() != invalid_hash1  # Won't match the full string
    if match2:
        assert match2.group() != invalid_hash2


# Test 6: Round-trip property for parse_hashes
@given(
    package_spec=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_.=/', min_size=1, max_size=50),
    algo=st.sampled_from(['sha256', 'sha384', 'sha512']),
    hash_val=st.text(alphabet='0123456789abcdef', min_size=64, max_size=64)
)
def test_parse_hashes_round_trip(package_spec, algo, hash_val):
    """Test that we can reconstruct equivalent line from parse_hashes output."""
    assume('--hash' not in package_spec)
    
    original_line = f"{package_spec} --hash={algo}:{hash_val}"
    cleaned_line, hashes = Parser.parse_hashes(original_line)
    
    # Reconstruct the line
    reconstructed = cleaned_line
    for h in hashes:
        reconstructed += " " + h
    
    # Parse again - should get same cleaned line
    cleaned_line2, hashes2 = Parser.parse_hashes(reconstructed)
    
    assert cleaned_line == cleaned_line2
    assert set(hashes) == set(hashes2)  # Order might differ


if __name__ == "__main__":
    print("Testing dparse.regex module...")
    print(f"HASH_REGEX pattern: {HASH_REGEX}")
    print("\nRunning property-based tests...")