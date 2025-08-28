"""Property-based tests for the packaging library using Hypothesis."""

import math
from hypothesis import assume, given, strategies as st, settings
import packaging.version
import packaging.requirements
import packaging.specifiers


# Strategy for valid version strings
# Based on PEP 440 version specification
def version_string_strategy():
    """Generate valid PEP 440 version strings."""
    # Simple version numbers like 1.0, 2.3.4
    simple = st.from_regex(r"[0-9]+(\.[0-9]+)*", fullmatch=True)
    
    # Pre-release versions
    pre_release = st.from_regex(
        r"[0-9]+(\.[0-9]+)*(a|b|rc)[0-9]+", 
        fullmatch=True
    )
    
    # Dev versions
    dev = st.from_regex(
        r"[0-9]+(\.[0-9]+)*\.dev[0-9]+",
        fullmatch=True
    )
    
    # Post versions
    post = st.from_regex(
        r"[0-9]+(\.[0-9]+)*\.post[0-9]+",
        fullmatch=True
    )
    
    # Combine all strategies
    return st.one_of(simple, pre_release, dev, post)


# Test 1: Version round-trip property
@given(version_string_strategy())
def test_version_round_trip(version_str):
    """Test that Version(str(Version(v))) == Version(v)"""
    v1 = packaging.version.Version(version_str)
    v2 = packaging.version.Version(str(v1))
    assert v1 == v2


# Test 2: Version comparison transitivity
@given(
    st.lists(version_string_strategy(), min_size=3, max_size=3, unique=True)
)
def test_version_comparison_transitivity(versions):
    """Test transitivity of version comparisons."""
    v1 = packaging.version.Version(versions[0])
    v2 = packaging.version.Version(versions[1])
    v3 = packaging.version.Version(versions[2])
    
    # Sort them to ensure v1 < v2 < v3
    sorted_versions = sorted([v1, v2, v3])
    v1, v2, v3 = sorted_versions
    
    # Check transitivity
    if v1 < v2 and v2 < v3:
        assert v1 < v3
    if v1 <= v2 and v2 <= v3:
        assert v1 <= v3


# Test 3: Version equality with trailing zeros
@given(st.integers(min_value=0, max_value=100))
def test_version_trailing_zeros_equality(major):
    """Test that versions with trailing zeros are equal."""
    v1 = packaging.version.Version(f"{major}.0")
    v2 = packaging.version.Version(f"{major}.0.0")
    v3 = packaging.version.Version(f"{major}.0.0.0")
    
    assert v1 == v2
    assert v2 == v3
    assert v1 == v3


# Strategy for requirement strings
def requirement_string_strategy():
    """Generate valid requirement strings."""
    # Package names (simplified)
    name = st.from_regex(r"[a-zA-Z][a-zA-Z0-9_-]*", fullmatch=True)
    
    # Version specifiers
    operator = st.sampled_from([">=", "<=", ">", "<", "==", "!="])
    version = version_string_strategy()
    specifier = st.builds(lambda op, ver: f"{op}{ver}", operator, version)
    
    # Multiple specifiers
    specifiers = st.lists(specifier, min_size=0, max_size=3).map(
        lambda specs: ",".join(specs)
    )
    
    # Extras
    extra_name = st.from_regex(r"[a-zA-Z][a-zA-Z0-9_-]*", fullmatch=True)
    extras = st.lists(extra_name, min_size=0, max_size=3, unique=True).map(
        lambda exts: f"[{','.join(exts)}]" if exts else ""
    )
    
    # Build requirement string
    return st.builds(
        lambda n, e, s: f"{n}{e}{s}",
        name, extras, specifiers
    )


# Test 4: Requirement round-trip property
@given(requirement_string_strategy())
def test_requirement_round_trip(req_str):
    """Test that Requirement(str(Requirement(r))) preserves semantics."""
    try:
        req1 = packaging.requirements.Requirement(req_str)
        req2 = packaging.requirements.Requirement(str(req1))
        
        # Check that key properties are preserved
        assert req1.name == req2.name
        assert req1.extras == req2.extras
        assert str(req1.specifier) == str(req2.specifier)
        assert req1.url == req2.url
    except packaging.requirements.InvalidRequirement:
        # Some generated strings might not be valid requirements
        assume(False)


# Test 5: Requirement extras normalization
@given(
    st.from_regex(r"[a-zA-Z][a-zA-Z0-9_-]*", fullmatch=True),
    st.lists(
        st.from_regex(r"[a-zA-Z][a-zA-Z0-9_-]*", fullmatch=True),
        min_size=1,
        max_size=5,
        unique=True
    )
)
def test_requirement_extras_normalization(name, extras):
    """Test that requirement extras are normalized to lowercase."""
    # Create requirement with mixed case extras
    mixed_case_extras = [e.upper() if i % 2 == 0 else e.lower() 
                        for i, e in enumerate(extras)]
    extras_str = f"[{','.join(mixed_case_extras)}]"
    req_str = f"{name}{extras_str}"
    
    req = packaging.requirements.Requirement(req_str)
    
    # Extras should be normalized to lowercase
    assert all(e.islower() for e in req.extras)
    
    # Check that the normalized extras match
    expected_extras = {e.lower() for e in mixed_case_extras}
    assert req.extras == expected_extras


# Test 6: SpecifierSet contains property
@given(
    st.lists(
        st.builds(
            lambda op, ver: f"{op}{ver}",
            st.sampled_from([">=", "<=", ">", "<", "==", "!="]),
            version_string_strategy()
        ),
        min_size=1,
        max_size=5
    ),
    version_string_strategy()
)
def test_specifierset_contains(specifiers, version_str):
    """Test that if a version satisfies a SpecifierSet, it satisfies at least one specifier."""
    spec_str = ",".join(specifiers)
    spec_set = packaging.specifiers.SpecifierSet(spec_str)
    version = packaging.version.Version(version_str)
    
    if version in spec_set:
        # If version is in the set, it should satisfy at least one individual specifier
        individual_satisfies = []
        for spec in specifiers:
            individual_spec = packaging.specifiers.SpecifierSet(spec)
            individual_satisfies.append(version in individual_spec)
        
        assert any(individual_satisfies), f"Version {version} is in {spec_set} but doesn't satisfy any individual specifier"


# Test 7: Version parse function is equivalent to Version constructor
@given(version_string_strategy())
def test_version_parse_equivalence(version_str):
    """Test that parse() and Version() produce equivalent results."""
    v1 = packaging.version.Version(version_str)
    v2 = packaging.version.parse(version_str)
    
    assert v1 == v2
    assert str(v1) == str(v2)
    assert repr(v1) == repr(v2)


# Test 8: Version ordering is total
@given(
    version_string_strategy(),
    version_string_strategy()
)
def test_version_total_ordering(v1_str, v2_str):
    """Test that version ordering is total (any two versions are comparable)."""
    v1 = packaging.version.Version(v1_str)
    v2 = packaging.version.Version(v2_str)
    
    # Exactly one of these should be true
    conditions = [v1 < v2, v1 == v2, v1 > v2]
    assert sum(conditions) == 1, f"Version ordering not total for {v1} and {v2}"


# Test 9: Version base_version removes pre/post/dev releases
@given(version_string_strategy())
def test_version_base_version_property(version_str):
    """Test that base_version removes pre-release, post-release, and dev release segments."""
    v = packaging.version.Version(version_str)
    base = packaging.version.Version(v.base_version)
    
    # Base version should not have pre, post, or dev parts
    assert not base.is_prerelease
    assert not base.is_postrelease
    assert not base.is_devrelease
    
    # Base version should be <= original version
    assert base <= v


if __name__ == "__main__":
    # Run the tests
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))