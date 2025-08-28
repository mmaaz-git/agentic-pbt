"""Additional edge case tests for packaging module to find potential bugs."""

from hypothesis import given, strategies as st, assume, settings
import packaging.version
import packaging.requirements
import packaging.specifiers


# Test for version string normalization inconsistencies
@given(st.integers(min_value=0, max_value=999))
def test_version_leading_zeros(num):
    """Test how versions handle leading zeros."""
    # Test with leading zeros
    padded = str(num).zfill(5)  # e.g., "00042"
    
    try:
        v1 = packaging.version.Version(padded)
        v2 = packaging.version.Version(str(num))
        
        # They should be equal semantically
        assert v1 == v2
        
        # But string representations might differ
        # This is where inconsistencies might show up
    except packaging.version.InvalidVersion:
        # Leading zeros might not be valid
        pass


# Test for extreme version numbers
@given(st.integers(min_value=0, max_value=10**100))
def test_version_extreme_numbers(num):
    """Test versions with extremely large numbers."""
    version_str = f"{num}.0.0"
    v = packaging.version.Version(version_str)
    
    # Should round-trip correctly
    assert packaging.version.Version(str(v)) == v


# Test empty version components
def test_version_empty_components():
    """Test various edge cases with empty or unusual version strings."""
    edge_cases = [
        "1..0",  # Double dots
        "1.",    # Trailing dot
        ".1",    # Leading dot
        "1.0.0.0.0.0.0.0.0.0",  # Many components
    ]
    
    for version_str in edge_cases:
        try:
            v = packaging.version.Version(version_str)
            # If it parses, it should round-trip
            assert packaging.version.Version(str(v)) == v
        except packaging.version.InvalidVersion:
            # These might be invalid, which is fine
            pass


# Test version comparison edge cases
@given(
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=1000)
)
def test_version_numeric_comparison(major, minor):
    """Test that numeric comparison works correctly."""
    v1 = packaging.version.Version(f"{major}.{minor}")
    v2 = packaging.version.Version(f"{major}.{minor + 1}")
    
    if minor < 1000:  # Avoid overflow
        assert v1 < v2
        assert not v1 > v2
        assert not v1 == v2


# Test requirement with unusual package names
@given(st.from_regex(r"[a-zA-Z]([a-zA-Z0-9._-]*[a-zA-Z0-9])?", fullmatch=True))
def test_requirement_package_names(name):
    """Test requirements with various package name formats."""
    # Package names with dots, underscores, hyphens
    req_str = f"{name}>=1.0"
    
    try:
        req = packaging.requirements.Requirement(req_str)
        # Name should be preserved
        assert req.name == name
        
        # Should round-trip
        req2 = packaging.requirements.Requirement(str(req))
        assert req.name == req2.name
    except packaging.requirements.InvalidRequirement:
        # Some names might be invalid
        pass


# Test specifier set edge cases
def test_specifierset_contradictions():
    """Test contradictory specifier sets."""
    # Create impossible specifier sets
    contradictions = [
        ">2.0,<1.0",  # Impossible range
        "==1.0,==2.0",  # Can't be two versions at once
        ">=3.0,<2.0",  # Empty range
    ]
    
    for spec_str in contradictions:
        spec_set = packaging.specifiers.SpecifierSet(spec_str)
        
        # No version should satisfy contradictory requirements
        test_versions = ["0.1", "1.0", "1.5", "2.0", "2.5", "3.0", "10.0"]
        for v_str in test_versions:
            v = packaging.version.Version(v_str)
            assert v not in spec_set, f"Version {v} unexpectedly satisfies contradictory specifier {spec_str}"


# Test version with all components
@given(
    st.integers(min_value=0, max_value=10),
    st.integers(min_value=0, max_value=10),
    st.integers(min_value=0, max_value=10),
    st.sampled_from(["a", "b", "rc"]),
    st.integers(min_value=0, max_value=10)
)
def test_version_complex_parsing(major, minor, micro, pre_type, pre_num):
    """Test complex version strings with multiple components."""
    # Build a complex version
    version_str = f"{major}.{minor}.{micro}{pre_type}{pre_num}"
    
    v = packaging.version.Version(version_str)
    
    # Check properties
    assert v.is_prerelease
    assert not v.is_postrelease
    assert not v.is_devrelease
    
    # Base version should strip pre-release
    base = packaging.version.Version(v.base_version)
    assert not base.is_prerelease
    assert base > v  # Pre-releases come before their base


# Test requirement URL parsing
def test_requirement_url_edge_cases():
    """Test requirement parsing with URLs."""
    test_cases = [
        "pkg @ https://example.com/pkg.tar.gz",
        "pkg @ file:///path/to/pkg",
        "pkg[extra] @ https://example.com/pkg.zip",
    ]
    
    for req_str in test_cases:
        req = packaging.requirements.Requirement(req_str)
        assert req.url is not None
        
        # URL should be preserved in string representation
        assert "@" in str(req)


# Test local version identifiers
@given(st.from_regex(r"[0-9]+\.[0-9]+\+[a-zA-Z0-9.]+", fullmatch=True))
def test_version_local_identifiers(version_str):
    """Test versions with local identifiers (1.0+local)."""
    try:
        v = packaging.version.Version(version_str)
        
        # Local versions should have local property
        assert v.local is not None
        
        # Should round-trip
        assert packaging.version.Version(str(v)) == v
    except packaging.version.InvalidVersion:
        # Some formats might be invalid
        pass


# Test epoch versions
@given(st.integers(min_value=1, max_value=10))
def test_version_epoch(epoch):
    """Test versions with epoch markers."""
    version_str = f"{epoch}!1.0"
    
    v = packaging.version.Version(version_str)
    
    # Epoch should affect sorting
    v_no_epoch = packaging.version.Version("1.0")
    assert v > v_no_epoch  # Epoch versions sort higher
    
    # Should round-trip
    assert packaging.version.Version(str(v)) == v


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))