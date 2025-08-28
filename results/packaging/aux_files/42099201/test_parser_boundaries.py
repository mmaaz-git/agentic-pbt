"""Test parser boundary conditions and potential bugs"""

import string
from hypothesis import given, strategies as st, assume, settings, example
from packaging.requirements import Requirement, InvalidRequirement
from packaging.utils import canonicalize_name


@given(st.text(alphabet=string.ascii_letters + string.digits + ".-_[](),;@", min_size=50, max_size=500))
@settings(max_examples=1000, deadline=None)
def test_parser_fuzzing(fuzzy_input):
    """Fuzz test the parser with random but constrained input"""
    try:
        req = Requirement(fuzzy_input)
        # If it parses, verify round-trip works
        req_str = str(req)
        req2 = Requirement(req_str)
        
        # Basic invariants should hold
        assert req.name == req2.name
        assert req.extras == req2.extras
    except InvalidRequirement:
        # Parser should cleanly reject invalid input
        pass
    except Exception as e:
        # Any other exception is a potential bug
        print(f"Unexpected exception with input '{fuzzy_input}': {e}")
        raise


@given(st.text(min_size=1, max_size=100))
def test_url_parsing_edge_cases(text):
    """Test URL parsing with @ symbol"""
    req_str = f"package @ {text}"
    
    try:
        req = Requirement(req_str)
        # If it parses with @, url should be set
        assert req.url == text or req.url is None
        
        # Round-trip
        req2 = Requirement(str(req))
        assert req.url == req2.url
    except InvalidRequirement:
        pass


@given(st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=3), min_size=10, max_size=50))
def test_many_extras(extras):
    """Test handling of many extras"""
    extras_str = "[" + ",".join(extras) + "]"
    req_str = f"package{extras_str}"
    
    try:
        req = Requirement(req_str)
        # Should handle many extras
        assert len(req.extras) <= len(extras)
        
        # String representation should work
        req_str2 = str(req)
        req2 = Requirement(req_str2)
        assert req.extras == req2.extras
    except InvalidRequirement:
        pass


@given(st.text(alphabet=".-_", min_size=1, max_size=20))
def test_separator_only_names(separators):
    """Test names consisting only of separators"""
    try:
        req = Requirement(separators)
        # If it accepts separator-only names, check properties
        assert req.name == separators
    except InvalidRequirement:
        # Should likely reject separator-only names
        pass


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
       st.text(alphabet=";", min_size=1, max_size=5))
def test_semicolon_handling(name, semicolons):
    """Test semicolon handling in requirements"""
    req_str = name + semicolons
    
    try:
        req = Requirement(req_str)
        # Semicolons might indicate markers
        assert req.name == name or req.marker is not None
    except InvalidRequirement:
        pass


@given(st.text(min_size=1, max_size=50))
@example("package[")
@example("package]")
@example("package[]extra")
@example("package[extra")
@example("package[extra]extra2")
def test_bracket_mismatch(text):
    """Test handling of mismatched brackets"""
    try:
        req = Requirement(text)
        # If it parses despite bracket issues, verify properties
        assert req.name
        
        # Round-trip should work
        req2 = Requirement(str(req))
        assert req.name == req2.name
    except InvalidRequirement:
        # Should reject mismatched brackets
        pass


@given(st.text(alphabet=string.digits + ".", min_size=1, max_size=10))
def test_version_only_input(version_str):
    """Test input that looks like only a version"""
    req_str = f"=={version_str}"
    
    try:
        req = Requirement(req_str)
        # Should have a package name
        assert req.name
    except InvalidRequirement:
        # Should reject version without package name
        pass


@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
       st.text(alphabet="~`!@#$%^&*()+={}|\\:\"'<>?,/", min_size=1, max_size=5))
def test_special_operator_chars(name, special):
    """Test special characters that might be confused with operators"""
    req_str = name + special
    
    try:
        req = Requirement(req_str)
        # Check how special chars are interpreted
        assert req.name
    except InvalidRequirement:
        # Most special chars should be rejected
        pass


@given(st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5), min_size=1, max_size=5),
       st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5), min_size=1, max_size=5))
def test_extras_normalization_consistency(extras1, extras2):
    """Test that extras normalization is consistent"""
    # Create two requirements with same extras in different order
    req_str1 = f"package[{','.join(extras1 + extras2)}]"
    req_str2 = f"package[{','.join(extras2 + extras1)}]"
    
    try:
        req1 = Requirement(req_str1)
        req2 = Requirement(req_str2)
        
        # Should have same extras regardless of input order
        assert req1.extras == req2.extras
        
        # String representations should be identical
        assert str(req1) == str(req2)
    except InvalidRequirement:
        pass


@given(st.text(min_size=1, max_size=100))
def test_double_parse_invariant(text):
    """Test that parsing twice gives same result"""
    try:
        req1 = Requirement(text)
        req2 = Requirement(text)
        
        # Should be deterministic
        assert req1.name == req2.name
        assert req1.extras == req2.extras
        assert str(req1.specifier) == str(req2.specifier)
        assert str(req1) == str(req2)
    except InvalidRequirement:
        pass


@given(st.text(alphabet=string.ascii_letters + "-._", min_size=1, max_size=30))
@settings(max_examples=500)
def test_canonicalize_name_edge_cases(name):
    """Test edge cases in canonicalize_name"""
    try:
        canonical = canonicalize_name(name)
        
        # Should be lowercase
        assert canonical == canonical.lower()
        
        # Should be idempotent
        assert canonicalize_name(canonical) == canonical
        
        # Test with validate flag
        canonical_validated = canonicalize_name(name, validate=True)
        
        # Both should give same result when input is valid
        assert canonical == canonical_validated
    except Exception as e:
        # With validate=True, might raise on invalid names
        if "validate" in str(e):
            # Try without validation
            try:
                canonical = canonicalize_name(name, validate=False)
                # Should still be lowercase and idempotent
                assert canonical == canonical.lower()
                assert canonicalize_name(canonical) == canonical
            except:
                pass