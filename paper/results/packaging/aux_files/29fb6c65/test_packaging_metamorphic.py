"""Metamorphic and invariant property tests for packaging module."""

from hypothesis import given, strategies as st, assume, settings, example
import packaging.version
import packaging.requirements
import packaging.specifiers
import packaging.utils


# Metamorphic property: canonicalization should be idempotent
@given(st.text(min_size=1, max_size=100))
def test_canonicalize_idempotent(name):
    """Test that canonicalize_name is idempotent."""
    canonical1 = packaging.utils.canonicalize_name(name)
    canonical2 = packaging.utils.canonicalize_name(canonical1)
    
    assert canonical1 == canonical2, f"Canonicalization not idempotent: {name} -> {canonical1} -> {canonical2}"


# Test version comparison with string manipulation
@given(st.integers(min_value=0, max_value=100))
def test_version_string_manipulation(num):
    """Test that certain string manipulations preserve version equality."""
    # Different representations of the same version
    v1 = packaging.version.Version(f"{num}")
    v2 = packaging.version.Version(f"{num}.0")
    v3 = packaging.version.Version(f"{num}.0.0")
    v4 = packaging.version.Version(f"{num}.0.0.0")
    
    # All should be equal
    assert v1 == v2 == v3 == v4
    
    # But their string representations should maintain format
    assert str(v1) == str(num)
    assert str(v2) == f"{num}.0"


# Helper for version strings
def version_string_strategy():
    """Generate valid PEP 440 version strings."""
    simple = st.from_regex(r"[0-9]+(\.[0-9]+)*", fullmatch=True)
    pre_release = st.from_regex(r"[0-9]+(\.[0-9]+)*(a|b|rc)[0-9]+", fullmatch=True)
    dev = st.from_regex(r"[0-9]+(\.[0-9]+)*\.dev[0-9]+", fullmatch=True)
    post = st.from_regex(r"[0-9]+(\.[0-9]+)*\.post[0-9]+", fullmatch=True)
    return st.one_of(simple, pre_release, dev, post)


# Test specifier set union and intersection properties
@given(
    version_string_strategy(),
    st.lists(
        st.builds(
            lambda op, ver: f"{op}{ver}",
            st.sampled_from([">=", "<=", ">", "<", "==", "!="]),
            version_string_strategy()
        ),
        min_size=1,
        max_size=3
    )
)
def test_specifierset_split_equivalence(version_str, specifiers):
    """Test that a combined specifier set is equivalent to individual checks."""
    # Create combined specifier
    combined = packaging.specifiers.SpecifierSet(",".join(specifiers))
    version = packaging.version.Version(version_str)
    
    # Create individual specifiers
    individuals = [packaging.specifiers.SpecifierSet(s) for s in specifiers]
    
    # Version is in combined iff it's in ALL individuals (AND logic)
    in_combined = version in combined
    in_all_individuals = all(version in spec for spec in individuals)
    
    assert in_combined == in_all_individuals


# Test requirement with whitespace
@given(
    st.from_regex(r"[a-zA-Z][a-zA-Z0-9_-]*", fullmatch=True),
    st.sampled_from([">=", "<=", ">", "<", "==", "!="]),
    version_string_strategy()
)
def test_requirement_whitespace_normalization(name, op, version):
    """Test that requirements handle whitespace consistently."""
    # Different whitespace patterns
    req1 = packaging.requirements.Requirement(f"{name}{op}{version}")
    req2 = packaging.requirements.Requirement(f"{name} {op} {version}")
    req3 = packaging.requirements.Requirement(f"{name}  {op}  {version}")
    
    # All should have the same specifier
    assert str(req1.specifier) == str(req2.specifier) == str(req3.specifier)
    assert req1.name == req2.name == req3.name


# Test version comparison with pre-releases
@given(
    st.integers(min_value=0, max_value=100),
    st.sampled_from(["a", "b", "rc"]),
    st.integers(min_value=0, max_value=10)
)
def test_version_prerelease_ordering(major, pre_type, pre_num):
    """Test that pre-release versions are ordered correctly."""
    # Create versions
    pre_version = packaging.version.Version(f"{major}.0{pre_type}{pre_num}")
    final_version = packaging.version.Version(f"{major}.0")
    next_version = packaging.version.Version(f"{major}.1")
    
    # Pre-release should be less than final
    assert pre_version < final_version
    
    # Final should be less than next minor
    assert final_version < next_version
    
    # Transitivity
    assert pre_version < next_version


# Test for version parsing robustness
@given(st.text(min_size=1, max_size=50))
def test_version_invalid_string_handling(text):
    """Test that invalid version strings are properly rejected."""
    try:
        v = packaging.version.Version(text)
        # If it parsed, it should round-trip
        v2 = packaging.version.Version(str(v))
        assert v == v2
    except packaging.version.InvalidVersion:
        # Should consistently fail
        try:
            v = packaging.version.Version(text)
            assert False, f"Inconsistent parsing of {text}"
        except packaging.version.InvalidVersion:
            pass  # Good, consistently invalid


# Test canonicalization properties
@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50)
)
def test_canonicalize_equivalence(name1, name2):
    """Test canonicalization equivalence properties."""
    canon1 = packaging.utils.canonicalize_name(name1)
    canon2 = packaging.utils.canonicalize_name(name2)
    
    # If canonical forms are equal, re-canonicalizing either input should give same result
    if canon1 == canon2:
        assert packaging.utils.canonicalize_name(name2) == canon1
        assert packaging.utils.canonicalize_name(name1) == canon2


# Test version inequality implies not equal
@given(version_string_strategy(), version_string_strategy())
def test_version_inequality_consistency(v1_str, v2_str):
    """Test that inequality relations are consistent."""
    v1 = packaging.version.Version(v1_str)
    v2 = packaging.version.Version(v2_str)
    
    # If v1 < v2, then v1 != v2 and not v1 > v2
    if v1 < v2:
        assert v1 != v2
        assert not v1 > v2
        assert not v1 == v2
        assert v1 <= v2
    
    # If v1 == v2, then not v1 < v2 and not v1 > v2
    if v1 == v2:
        assert not v1 < v2
        assert not v1 > v2
        assert v1 <= v2
        assert v1 >= v2


# Test specifier normalization
@given(
    st.sampled_from([">=", "<=", ">", "<", "==", "!="]),
    version_string_strategy()
)
def test_specifier_string_consistency(op, version):
    """Test that specifier string representation is consistent."""
    spec1 = packaging.specifiers.SpecifierSet(f"{op}{version}")
    spec2 = packaging.specifiers.SpecifierSet(f" {op} {version} ")  # With spaces
    
    # String representations should be normalized
    # Note: This might reveal inconsistencies in normalization
    str1 = str(spec1)
    str2 = str(spec2)
    
    # Parse the strings again
    spec1_reparsed = packaging.specifiers.SpecifierSet(str1)
    spec2_reparsed = packaging.specifiers.SpecifierSet(str2)
    
    # Should be functionally equivalent
    test_versions = ["0.1", "1.0", "2.0", "10.0"]
    for v_str in test_versions:
        v = packaging.version.Version(v_str)
        assert (v in spec1) == (v in spec2) == (v in spec1_reparsed) == (v in spec2_reparsed)


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))