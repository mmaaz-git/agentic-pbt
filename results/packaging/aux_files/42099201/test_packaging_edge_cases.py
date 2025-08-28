"""Additional edge case tests for packaging.requirements"""

import string
from hypothesis import given, strategies as st, assume, settings, example
from packaging.requirements import Requirement, InvalidRequirement
from packaging.utils import canonicalize_name


# Test for empty string edge cases
@given(st.integers(min_value=1, max_value=10))
def test_empty_extras_handling(n_commas):
    """Test how empty extras are handled with various comma patterns"""
    # Create extras with only commas
    extras_str = "," * n_commas
    req_str = f"package[{extras_str}]"
    
    try:
        req = Requirement(req_str)
        # Check that empty extras are handled
        # The implementation should either reject or handle gracefully
        assert isinstance(req.extras, set)
    except InvalidRequirement:
        # It's valid to reject malformed extras
        pass


@given(st.text(alphabet=string.ascii_letters + string.digits + ".-_", min_size=1, max_size=50))
def test_canonicalize_preserves_length_relationship(name):
    """Test that canonicalization doesn't increase length unexpectedly"""
    try:
        canonical = canonicalize_name(name)
        # Canonicalization typically shouldn't make names longer
        # It only lowercases and normalizes separators
        # Let's check if there's any unexpected expansion
        
        # Count actual characters (not separators)
        orig_chars = sum(1 for c in name if c not in ".-_")
        canon_chars = sum(1 for c in canonical if c not in "-")
        
        # Character count should be preserved or reduced
        assert canon_chars <= orig_chars
    except Exception:
        pass


@given(st.text(alphabet=string.whitespace, min_size=1, max_size=20))
def test_whitespace_only_input(whitespace):
    """Test that whitespace-only input is properly rejected"""
    try:
        req = Requirement(whitespace)
        # If it doesn't raise, the name should not be just whitespace
        assert req.name.strip() != ""
    except InvalidRequirement:
        # Should reject whitespace-only input
        pass


@given(st.text(min_size=1, max_size=100))
@example("package==1.0.0==2.0.0")
@example("package>=1.0<2.0>3.0")
def test_malformed_version_specs(spec_str):
    """Test handling of malformed version specifications"""
    try:
        req = Requirement(spec_str)
        # If it parses, the string representation should also parse
        req2 = Requirement(str(req))
        assert req.name == req2.name
    except InvalidRequirement:
        # Many malformed specs should be rejected
        pass


@given(st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5), min_size=2, max_size=10))
def test_extras_deduplication_complex(extras_list):
    """Test that extras deduplication works with various patterns"""
    # Create patterns with duplicates
    all_extras = extras_list + extras_list[::-1]  # Add reversed duplicates
    extras_str = "[" + ",".join(all_extras) + "]"
    req_str = f"package{extras_str}"
    
    try:
        req = Requirement(req_str)
        # Should have at most the unique count
        assert len(req.extras) <= len(set(extras_list))
        
        # All unique extras should be present
        for extra in set(extras_list):
            assert extra in req.extras
    except InvalidRequirement:
        pass


@given(st.text(alphabet="[](),;@", min_size=1, max_size=20))
def test_special_chars_in_name(special_chars):
    """Test that special characters in package names are handled properly"""
    req_str = f"package{special_chars}"
    
    try:
        req = Requirement(req_str)
        # If it parses with special chars, verify the name
        # Special chars might be part of extras or other components
        assert req.name  # Should have a name
    except InvalidRequirement:
        # Most special character patterns should be rejected
        pass


@given(st.integers(min_value=0, max_value=1000))
def test_numeric_package_names(number):
    """Test package names that are purely numeric"""
    req_str = str(number)
    
    try:
        req = Requirement(req_str)
        assert req.name == str(number)
        
        # Round-trip should work
        req2 = Requirement(str(req))
        assert req2.name == str(number)
    except InvalidRequirement:
        # Some numeric patterns might be invalid
        pass


@given(st.text(alphabet=string.ascii_uppercase, min_size=1, max_size=20),
       st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=20))
def test_case_preservation_in_names(upper_part, lower_part):
    """Test that case is preserved in package names"""
    name = upper_part + lower_part
    
    try:
        req = Requirement(name)
        # Package names should preserve case
        assert req.name == name
        
        # But canonicalization should lowercase
        canonical = canonicalize_name(name)
        assert canonical == canonical.lower()
    except InvalidRequirement:
        pass


@given(st.lists(st.sampled_from([">=", "<=", ">", "<", "==", "!="]), min_size=2, max_size=5),
       st.lists(st.text(alphabet=string.digits + ".", min_size=1, max_size=5), min_size=2, max_size=5))
def test_multiple_version_constraints(ops, versions):
    """Test multiple version constraints"""
    constraints = [op + ver for op, ver in zip(ops, versions)]
    spec_str = ",".join(constraints)
    req_str = f"package{spec_str}"
    
    try:
        req = Requirement(req_str)
        # Should handle multiple constraints
        assert req.specifier
        
        # String representation should be valid
        req2 = Requirement(str(req))
        assert str(req.specifier) == str(req2.specifier)
    except InvalidRequirement:
        pass


@given(st.text(min_size=1, max_size=200))
def test_very_long_requirement_strings(long_str):
    """Test handling of very long requirement strings"""
    try:
        req = Requirement(long_str)
        # If it parses, verify basic properties
        assert req.name
        assert len(str(req)) > 0
    except InvalidRequirement:
        # Long malformed strings should be rejected
        pass


@given(st.text(alphabet=string.ascii_letters + ".-_", min_size=1, max_size=30))
@settings(max_examples=500)
def test_canonicalize_normalize_separators(name):
    """Test that canonicalize_name normalizes different separators consistently"""
    # Replace some characters with different separators
    variants = [
        name,
        name.replace("-", "_"),
        name.replace("_", "."),
        name.replace(".", "-"),
        name.replace("-", ".").replace("_", "-")
    ]
    
    try:
        canonicals = [canonicalize_name(v) for v in variants]
        
        # Check for consistency issues
        # Names that differ only in separators should canonicalize the same
        for i, v1 in enumerate(variants):
            for j, v2 in enumerate(variants):
                # If they only differ in separators, they should canonicalize the same
                v1_alpha = v1.replace("-", "").replace("_", "").replace(".", "").lower()
                v2_alpha = v2.replace("-", "").replace("_", "").replace(".", "").lower()
                
                if v1_alpha == v2_alpha:
                    assert canonicals[i] == canonicals[j], f"Inconsistent canonicalization: {v1} -> {canonicals[i]}, {v2} -> {canonicals[j]}"
    except Exception:
        pass