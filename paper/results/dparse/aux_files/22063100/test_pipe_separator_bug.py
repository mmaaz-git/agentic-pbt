#!/usr/bin/env python3
"""
Demonstrate the pipe separator bug in dparse.regex.

The regex pattern [=| ] is likely a typo - it matches '=', '|', or ' '.
It should probably be [= ] to match only '=' or ' '.
"""

import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from dparse.regex import HASH_REGEX
from dparse.parser import Parser


def demonstrate_pipe_bug():
    """Demonstrate that the regex incorrectly matches pipe separator."""
    
    print("HASH_REGEX pattern:", HASH_REGEX)
    print("Pattern breakdown: --hash[=| ]\\w+:\\w+")
    print("  [=| ] is a character class that matches:")
    print("    '=' - correct for --hash=sha256:...")
    print("    ' ' - correct for --hash sha256:...")  
    print("    '|' - INCORRECT! pip never uses --hash|sha256:...")
    print()
    
    # Valid pip formats (should match)
    valid_formats = [
        "--hash=sha256:abc123",
        "--hash sha256:abc123",
    ]
    
    # Invalid format that incorrectly matches due to bug
    invalid_format = "--hash|sha256:abc123"
    
    print("Testing valid pip formats:")
    for fmt in valid_formats:
        match = re.search(HASH_REGEX, fmt)
        print(f"  {fmt:<30} -> {'MATCH' if match else 'NO MATCH'}")
    
    print("\nTesting invalid format with pipe separator:")
    match = re.search(HASH_REGEX, invalid_format)
    print(f"  {invalid_format:<30} -> {'MATCH' if match else 'NO MATCH'}")
    
    if match:
        print("\n🐛 BUG CONFIRMED: Regex matches pipe separator which pip doesn't use!")
        print(f"   Matched: '{match.group()}'")
        
        # Show how this affects parse_hashes
        print("\nDemonstrating impact on parse_hashes:")
        line_with_pipe = "package==1.0.0 --hash|sha256:abcdef123456"
        cleaned, hashes = Parser.parse_hashes(line_with_pipe)
        print(f"  Input:  '{line_with_pipe}'")
        print(f"  Output: '{cleaned}'")
        print(f"  Hashes: {hashes}")
        
        return True
    
    return False


def test_character_class_interpretation():
    """Test what the [=| ] character class actually matches."""
    
    print("\nDetailed analysis of [=| ] character class:")
    print("The pattern [=| ] is often misunderstood.")
    print("It does NOT mean '= OR <space>'")
    print("It means 'any character from the set {=, |, space}'")
    
    test_chars = ['=', ' ', '|', 'X', '-', '_']
    pattern = r'[=| ]'
    
    print("\nCharacter matching test:")
    for char in test_chars:
        match = re.search(pattern, char)
        result = "MATCH" if match else "NO MATCH"
        print(f"  '{char}' -> {result}")
    
    print("\nThis is likely a typo. The intended pattern was probably:")
    print("  [= ]   - matches '=' or space")
    print("  OR")
    print("  (?:=| ) - matches '=' or space using group syntax")


def check_real_world_impact():
    """Check if this bug could affect real-world usage."""
    
    print("\n" + "="*60)
    print("REAL-WORLD IMPACT ANALYSIS")
    print("="*60)
    
    # Simulate a requirements file line with accidental pipe
    test_lines = [
        "django==3.2.0 --hash|sha256:abc123",  # Typo: used | instead of =
        "flask>=2.0 --hash |sha256:def456",    # Space before pipe
        "requests --hash| sha256:ghi789",      # Space after pipe
    ]
    
    print("Testing lines that might occur due to typos:")
    for line in test_lines:
        cleaned, hashes = Parser.parse_hashes(line)
        print(f"\nInput:  {line}")
        print(f"Cleaned: {cleaned}")
        print(f"Hashes: {hashes}")
        
        if hashes:
            print("  ⚠️  Hash incorrectly extracted despite invalid format!")


if __name__ == "__main__":
    print("="*60)
    print("PIPE SEPARATOR BUG IN DPARSE.REGEX")
    print("="*60)
    print()
    
    bug_found = demonstrate_pipe_bug()
    test_character_class_interpretation()
    check_real_world_impact()
    
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    if bug_found:
        print("✓ Bug confirmed: The regex pattern [=| ] incorrectly matches pipe '|'")
        print("✓ This is likely a typo - should be [= ] to match only '=' or space")
        print("✓ Impact: Parser will incorrectly accept invalid hash formats with pipes")
        print("\nSuggested fix: Change HASH_REGEX from:")
        print("  r\"--hash[=| ]\\w+:\\w+\"")
        print("to:")
        print("  r\"--hash[= ]\\w+:\\w+\"")
    else:
        print("No bug found - regex works as expected")