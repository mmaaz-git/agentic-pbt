import pathlib
from hypothesis import given, strategies as st
import string

def test_with_suffix_crash_on_double_dot_files():
    """
    Demonstrates a crash bug in pathlib.PurePath.with_suffix()
    
    When a filename starts with two dots followed by text (like "..file"), 
    pathlib treats everything after the first dot as the suffix.
    This means "..file" has stem="." and suffix=".file".
    
    When with_suffix('') is called to remove the suffix, it tries to 
    call with_name('.'), which raises ValueError because '.' is not 
    a valid filename.
    """
    
    # Create a path with the problematic pattern
    p = pathlib.PurePath("..file")
    
    # Verify the parsing
    assert p.name == "..file"
    assert p.stem == "."
    assert p.suffix == ".file"
    
    # This should work but crashes
    try:
        result = p.with_suffix('')
        assert False, f"Expected crash but got: {result}"
    except ValueError as e:
        assert str(e) == "Invalid name '.'"
        print(f"✓ Confirmed crash: {e}")
        return True

def test_with_suffix_crash_multiple_cases():
    """Test multiple cases that trigger the crash"""
    
    crash_cases = [
        "..file",      # stem=".", suffix=".file"
        "..test",      # stem=".", suffix=".test"
        "..data",      # stem=".", suffix=".data"
        "..config",    # stem=".", suffix=".config"
    ]
    
    crashes = []
    
    for filename in crash_cases:
        p = pathlib.PurePath(filename)
        
        # All should have stem="." and a suffix
        assert p.stem == "."
        assert p.suffix == f".{filename[2:]}"
        
        # All should crash when trying to remove suffix
        try:
            p.with_suffix('')
            print(f"ERROR: {filename} didn't crash!")
        except ValueError as e:
            crashes.append(filename)
            print(f"✓ {filename} crashes as expected: {e}")
    
    assert len(crashes) == len(crash_cases), "Some cases didn't crash"
    return True

def test_with_suffix_other_operations():
    """Test that other operations on ..file work fine"""
    
    p = pathlib.PurePath("..file")
    
    # These operations should work
    assert p.with_suffix('.txt') == pathlib.PurePath('..txt')
    assert p.with_suffix('.new') == pathlib.PurePath('..new')
    
    # The crash only happens with empty suffix
    print("✓ Other with_suffix operations work fine")
    return True

def test_similar_patterns_that_work():
    """Test similar patterns that don't crash"""
    
    working_cases = [
        ".file",       # Hidden file - works fine
        "...file",     # Three dots - different parsing
        "a..file",     # Doesn't start with .. - works fine
        "../file",     # Path with .. directory - works fine
    ]
    
    for filename in working_cases:
        p = pathlib.PurePath(filename)
        
        try:
            result = p.with_suffix('')
            print(f"✓ {filename} -> with_suffix('') -> {result} (works)")
        except ValueError:
            print(f"✗ {filename} unexpectedly crashed")
            
    return True

@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10))
def test_double_dot_pattern_hypothesis(suffix_text):
    """Property test: ..X pattern always crashes with with_suffix('')"""
    
    # Create filename starting with .. followed by text
    filename = f"..{suffix_text}"
    p = pathlib.PurePath(filename)
    
    # This pattern should always have stem="." and suffix=f".{suffix_text}"
    assert p.stem == "."
    assert p.suffix == f".{suffix_text}"
    
    # And should always crash with with_suffix('')
    try:
        p.with_suffix('')
        assert False, f"Expected crash for {filename}"
    except ValueError as e:
        assert "Invalid name '.'" in str(e)

if __name__ == "__main__":
    print("Testing pathlib.PurePath.with_suffix() crash bug")
    print("=" * 60)
    
    test_with_suffix_crash_on_double_dot_files()
    print()
    
    test_with_suffix_crash_multiple_cases()
    print()
    
    test_with_suffix_other_operations()
    print()
    
    test_similar_patterns_that_work()
    print()
    
    # Run hypothesis test
    print("Running property-based test...")
    import pytest
    pytest.main([__file__, "-v", "-k", "hypothesis", "--tb=short", "-q"])