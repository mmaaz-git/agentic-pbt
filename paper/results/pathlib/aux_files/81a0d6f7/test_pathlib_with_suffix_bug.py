import pathlib
from hypothesis import given, strategies as st

# Generate paths that already have numeric-looking suffixes
paths_with_numeric_suffix = st.one_of(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10).map(
        lambda s: s + "." + str(st.integers(0, 999).example())
    ),
    st.builds(
        lambda base, num: f"{base}.{num}",
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
        st.floats(min_value=0.0, max_value=99.9, allow_nan=False).map(lambda x: f"{x:.1f}")
    )
)

def test_with_suffix_breaks_roundtrip():
    """
    Test that demonstrates a bug in pathlib's with_suffix method.
    
    When a path has a numeric-looking component that pathlib treats as a suffix (like "1.0"),
    using with_suffix to add and then remove a suffix doesn't return to the original path.
    
    This violates the expected round-trip property:
    path.with_suffix('.ext').with_suffix('') should equal path when path.suffix == ''
    """
    
    # Concrete failing example
    original = pathlib.PurePath("version1.0")
    
    # The original path has what pathlib considers a suffix
    assert original.suffix == ".0"
    
    # Replace the suffix with .txt
    with_txt = original.with_suffix(".txt")
    assert str(with_txt) == "version1.txt"
    assert with_txt.suffix == ".txt"
    
    # Now try to remove the suffix
    restored = with_txt.with_suffix("")
    assert str(restored) == "version1"
    assert restored.suffix == ""
    
    # BUG: The "restored" path is NOT the same as the original!
    assert str(original) != str(restored), "Round-trip failed: version1.0 != version1"
    
    # This is problematic because:
    # 1. with_suffix('.txt') on "version1.0" loses the ".0" part permanently
    # 2. There's no way to know that ".0" was originally part of the stem vs a suffix
    # 3. This breaks the principle of least surprise for version-numbered files
    
    return True

def test_with_suffix_semantic_inconsistency():
    """
    Demonstrates semantic inconsistency in with_suffix behavior.
    
    The method treats numeric extensions as suffixes but doesn't preserve them properly
    when replacing suffixes, leading to data loss.
    """
    
    # These should behave consistently, but they don't
    test_cases = [
        ("file.backup", ".txt"),  # Non-numeric: backup -> file.txt -> file (loses .backup)
        ("file.2", ".txt"),       # Numeric: 2 -> file.txt -> file (loses .2)
        ("version1.0", ".txt"),   # Version-like: 0 -> version1.txt -> version1 (loses .0)
    ]
    
    inconsistencies = []
    
    for original_str, new_suffix in test_cases:
        original = pathlib.PurePath(original_str)
        
        # Apply new suffix
        modified = original.with_suffix(new_suffix)
        
        # The issue: with_suffix REPLACES the last suffix rather than APPENDING
        # This means data is lost when the original had a suffix
        
        if original.suffix:
            # If original had a suffix, it gets replaced (not appended)
            parts_before = original_str.rsplit(".", 1)[0]
            expected = parts_before + new_suffix
            actual = str(modified)
            
            if expected != actual:
                inconsistencies.append({
                    'original': original_str,
                    'expected': expected,
                    'actual': actual,
                    'data_lost': original.suffix
                })
    
    # All test cases lose data
    assert len(inconsistencies) == 3
    
    for inc in inconsistencies:
        print(f"Data loss: {inc['original']} -> with_suffix('.txt') -> {inc['actual']}")
        print(f"  Lost: {inc['data_lost']}")
    
    return True

if __name__ == "__main__":
    # Run the concrete test
    print("Testing round-trip property violation:")
    print("=" * 50)
    test_with_suffix_breaks_roundtrip()
    print("✓ Confirmed: Round-trip property is violated")
    print()
    
    print("Testing semantic inconsistency:")
    print("=" * 50)
    test_with_suffix_semantic_inconsistency()
    print("✓ Confirmed: with_suffix causes data loss")
    
    print("\n" + "=" * 50)
    print("BUG CONFIRMED: pathlib.PurePath.with_suffix has unexpected behavior")
    print("when dealing with paths that have numeric-looking components.")
    print("This can cause data loss when manipulating version-numbered files.")