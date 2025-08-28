"""
Test for undocumented behavior of negative count/maxsplit parameters in re module.
"""
import re


def test_negative_count_prevents_substitution():
    """Negative count values prevent any substitutions (undocumented)."""
    string = 'aaa'
    pattern = 'a'
    replacement = 'b'
    
    # Test various negative values
    for count in [-1, -2, -100]:
        result = re.sub(pattern, replacement, string, count=count)
        assert result == string, f"count={count} should prevent substitution"
        
        result, n = re.subn(pattern, replacement, string, count=count)
        assert result == string, f"subn with count={count} should prevent substitution"
        assert n == 0, f"subn should report 0 substitutions with count={count}"
    
    # Contrast with count=0 (unlimited)
    result = re.sub(pattern, replacement, string, count=0)
    assert result == 'bbb', "count=0 should mean unlimited"
    
    print("✓ Confirmed: Negative count prevents substitutions (undocumented)")


def test_negative_maxsplit_prevents_splitting():
    """Negative maxsplit values prevent any splits (undocumented)."""
    string = '0,0,0'
    pattern = ','
    
    # Test various negative values
    for maxsplit in [-1, -2, -100]:
        result = re.split(pattern, string, maxsplit=maxsplit)
        assert result == [string], f"maxsplit={maxsplit} should prevent splitting"
    
    # Contrast with maxsplit=0 (unlimited)
    result = re.split(pattern, string, maxsplit=0)
    assert result == ['0', '0', '0'], "maxsplit=0 should mean unlimited"
    
    print("✓ Confirmed: Negative maxsplit prevents splits (undocumented)")


def test_documentation_inconsistency():
    """
    The documentation states "If maxsplit is nonzero, at most maxsplit splits occur"
    This implies negative values (being nonzero) should allow splits, but they don't.
    """
    string = 'a-b-c'
    pattern = '-'
    
    # According to docs, -1 is nonzero, so should allow splits
    result = re.split(pattern, string, maxsplit=-1)
    
    # But it doesn't split at all
    assert result == ['a-b-c'], "Negative maxsplit doesn't follow documented 'nonzero' behavior"
    
    print("✓ Confirmed: Documentation inconsistency with negative maxsplit")


if __name__ == '__main__':
    test_negative_count_prevents_substitution()
    test_negative_maxsplit_prevents_splitting()
    test_documentation_inconsistency()
    print("\nAll tests pass, confirming undocumented/inconsistent behavior with negative parameters")