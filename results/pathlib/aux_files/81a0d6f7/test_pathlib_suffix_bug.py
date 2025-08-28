import pathlib
from hypothesis import given, strategies as st, assume

# Generate numbers that look like version numbers when used as filenames
version_like = st.one_of(
    st.floats(min_value=0.1, max_value=99.9, allow_nan=False, allow_infinity=False)
    .map(lambda x: f"{x:.1f}"),  # "1.0", "2.5", etc
    st.tuples(
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99)
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}"),  # "1.2.3"
)

@given(version_like)
def test_with_suffix_empty_behavior(version):
    """
    Test: with_suffix('') should remove the suffix according to its documented behavior.
    
    The documentation states: "If the given suffix is an empty string, remove the suffix from the path."
    This should mean that after with_suffix(''), the path should have no suffix (suffix == '').
    """
    # Create a path with the version-like string and an extension
    p = pathlib.PurePath(version + ".txt")
    
    # Apply with_suffix('')
    p_no_suffix = p.with_suffix('')
    
    # According to the documentation, this should remove "the suffix"
    # But the actual behavior depends on what pathlib considers "the suffix"
    
    # The documentation is ambiguous here - does "remove the suffix" mean:
    # 1. Remove the last suffix only (current behavior)
    # 2. Remove all suffixes to have no suffix at all
    
    # Let's test for a potential inconsistency:
    # If with_suffix('') is meant to "remove the suffix", 
    # then the result should have suffix == ''
    
    if p.suffix == ".txt" and p_no_suffix.suffix != '':
        # This reveals the ambiguity/bug
        print(f"Bug found: {p} -> with_suffix('') -> {p_no_suffix} (suffix={p_no_suffix.suffix!r})")
        print(f"  Original suffixes: {p.suffixes}")
        print(f"  Result suffixes: {p_no_suffix.suffixes}")
        assert False, f"with_suffix('') didn't fully remove suffix: {p} -> {p_no_suffix} has suffix {p_no_suffix.suffix!r}"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])