#!/usr/bin/env python3
"""Focused tests to find bugs in dparse.regex and parse_hashes."""

import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from dparse.regex import HASH_REGEX
from dparse.parser import Parser


# Bug Hunt 1: Character class [=| ] bug
def test_pipe_separator_bug():
    """The regex [=| ] matches pipe '|' which is likely unintended."""
    # pip uses --hash=algo:value or --hash algo:value
    # but never --hash|algo:value
    
    # This should NOT match according to pip's specification
    pipe_hash = "--hash|sha256:abc123def456"
    match = re.search(HASH_REGEX, pipe_hash)
    
    print(f"Testing: {pipe_hash}")
    print(f"Match: {match.group() if match else 'None'}")
    
    # The bug: this matches but shouldn't
    assert match is not None, "BUG CONFIRMED: Regex matches pipe separator"
    return match.group() == pipe_hash


# Bug Hunt 2: Hash values with hyphens
@given(st.text(alphabet='0123456789abcdef-', min_size=64, max_size=64))
def test_hash_with_hyphens(hash_value):
    """Test if hashes with hyphens are handled correctly."""
    # Real hash values don't have hyphens, but what if they did?
    assume('-' in hash_value)
    
    hash_string = f"--hash=sha256:{hash_value}"
    match = re.search(HASH_REGEX, hash_string)
    
    # \w+ doesn't match hyphens, so this will fail to match full hash
    if match:
        # The match will be truncated at the first hyphen
        assert match.group() != hash_string


# Bug Hunt 3: Algorithm names with numbers
def test_algorithm_with_numbers():
    """Test algorithm names that contain numbers."""
    # Some algorithms have numbers like 'sha224', 'sha3_256'
    
    test_cases = [
        "--hash=sha224:abc123",
        "--hash=sha3_256:abc123",  # This will fail! underscore not in \w
        "--hash=blake2b:abc123",
        "--hash=md5:abc123"
    ]
    
    for test_case in test_cases:
        match = re.search(HASH_REGEX, test_case)
        print(f"Testing: {test_case}")
        print(f"Match: {match.group() if match else 'None'}")
        
        if '_' in test_case:
            # Underscore IS part of \w, so this should match
            if match:
                print(f"  Matched: {match.group()}")


# Bug Hunt 4: Base64 encoded hashes
def test_base64_hashes():
    """Test Base64 encoded hashes which use + and / and =."""
    # Base64 uses A-Z, a-z, 0-9, +, /, and = for padding
    
    base64_hashes = [
        "--hash=sha256:abc123def456ghi789+/=",
        "--hash=sha256:SGVsbG8gV29ybGQh",  # Valid base64
        "--hash=sha256:YWJjZGVmZ2hpams+Pw==",  # With padding
    ]
    
    for hash_string in base64_hashes:
        match = re.search(HASH_REGEX, hash_string)
        print(f"Testing: {hash_string}")
        
        if match:
            matched_text = match.group()
            print(f"  Matched: {matched_text}")
            
            # Bug: \w+ doesn't match +, /, or =
            # So base64 hashes will be truncated
            if any(c in hash_string for c in ['+', '/', '=']):
                if matched_text == hash_string:
                    print(f"  ERROR: Should have truncated at special chars!")
                else:
                    print(f"  CONFIRMED: Truncated at special chars")


# Bug Hunt 5: Unicode in hash values  
@given(st.text(min_size=1, max_size=10))
def test_unicode_in_hashes(text):
    """Test what happens with Unicode characters."""
    # Filter to only unicode
    assume(any(ord(c) > 127 for c in text))
    
    hash_string = f"--hash=sha256:{text}abc123"
    match = re.search(HASH_REGEX, hash_string)
    
    # \w in Python 3 matches Unicode word characters by default!
    # This might match more than intended
    if match:
        print(f"Unicode test: {repr(hash_string)}")
        print(f"  Matched: {repr(match.group())}")


# Bug Hunt 6: Multiple spaces or tabs
def test_whitespace_variations():
    """Test various whitespace between --hash and algorithm."""
    
    test_cases = [
        "--hash  sha256:abc123",  # Double space
        "--hash\tsha256:abc123",   # Tab
        "--hash sha256:abc123",    # Normal space
        "--hash=sha256:abc123",    # Equals
    ]
    
    for test_case in test_cases:
        match = re.search(HASH_REGEX, test_case)
        print(f"Testing: {repr(test_case)}")
        
        # The regex [=| ] only matches single char, not multiple spaces
        if '\t' in test_case or '  ' in test_case:
            # Tab or double space won't match
            assert match is None, f"Should not match: {test_case}"
        else:
            assert match is not None, f"Should match: {test_case}"


# Bug Hunt 7: Colon variations
def test_colon_variations():
    """Test what happens with multiple or missing colons."""
    
    test_cases = [
        "--hash=sha256::abc123",     # Double colon
        "--hash=sha256:abc:123",     # Extra colon in hash
        "--hash=sha256abc123",       # Missing colon
        "--hash=:abc123",            # Missing algorithm
        "--hash=sha256:",            # Missing hash value
    ]
    
    for test_case in test_cases:
        match = re.search(HASH_REGEX, test_case)
        print(f"Testing: {repr(test_case)}")
        if match:
            print(f"  Matched: {match.group()}")


# Bug Hunt 8: Case sensitivity
def test_case_sensitivity():
    """Test uppercase vs lowercase in hash specifications."""
    
    test_cases = [
        "--hash=SHA256:ABC123DEF",  # Uppercase algo and hash
        "--HASH=sha256:abc123",     # Uppercase --HASH
        "--Hash=sha256:abc123",     # Mixed case
    ]
    
    for test_case in test_cases:
        match = re.search(HASH_REGEX, test_case)
        print(f"Testing: {test_case}")
        
        # The regex is case-sensitive for '--hash'
        if test_case.startswith("--hash"):
            assert match is not None, f"Should match: {test_case}"
        else:
            assert match is None, f"Should not match: {test_case}"


if __name__ == "__main__":
    print("=" * 60)
    print("BUG HUNTING IN DPARSE.REGEX")
    print("=" * 60)
    print(f"HASH_REGEX pattern: {HASH_REGEX}")
    print("=" * 60)
    
    print("\n1. PIPE SEPARATOR BUG TEST:")
    test_pipe_separator_bug()
    
    print("\n2. ALGORITHM NAMES WITH NUMBERS/UNDERSCORES:")
    test_algorithm_with_numbers()
    
    print("\n3. BASE64 ENCODED HASHES:")
    test_base64_hashes()
    
    print("\n4. WHITESPACE VARIATIONS:")
    test_whitespace_variations()
    
    print("\n5. COLON VARIATIONS:")
    test_colon_variations()
    
    print("\n6. CASE SENSITIVITY:")
    test_case_sensitivity()
    
    print("\n" + "=" * 60)
    print("SUMMARY OF FINDINGS")
    print("=" * 60)