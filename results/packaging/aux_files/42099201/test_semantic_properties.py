"""Test semantic properties and transformations"""

from hypothesis import given, strategies as st, assume, settings
from packaging.requirements import Requirement, InvalidRequirement
from packaging.specifiers import SpecifierSet
import string


@given(st.text(alphabet=string.ascii_letters + string.digits + ".-_", min_size=1, max_size=20),
       st.lists(st.text(alphabet=string.digits + ".*", min_size=1, max_size=10), min_size=2, max_size=5))
def test_specifier_normalization_preserves_semantics(name, versions):
    """Test that specifier normalization preserves semantic meaning"""
    # Create various equivalent specifiers
    specs = [
        f">={versions[0]},<={versions[1]}",  # Range
        f"<={versions[1]},>={versions[0]}",  # Reversed order
        f">={versions[0]}, <={versions[1]}",  # With space
    ]
    
    reqs = []
    for spec in specs:
        req_str = name + spec
        try:
            req = Requirement(req_str)
            reqs.append(req)
        except InvalidRequirement:
            pass
    
    if len(reqs) >= 2:
        # All should have same semantic meaning
        for i in range(1, len(reqs)):
            # The specifier sets should be equivalent
            assert str(reqs[0].specifier) == str(reqs[i].specifier), \
                f"Specifiers differ: {reqs[0].specifier} != {reqs[i].specifier}"


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
       st.lists(st.text(alphabet=string.ascii_lowercase + "_", min_size=1, max_size=5), min_size=2, max_size=10))
def test_duplicate_extras_semantic(name, extras):
    """Test semantic handling of duplicate extras"""
    # Create requirement with duplicates
    extras_with_dups = extras + extras + extras  # Triple everything
    req_str = f"{name}[{','.join(extras_with_dups)}]"
    
    try:
        req = Requirement(req_str)
        
        # Should have only unique extras
        assert len(req.extras) == len(set(extras))
        
        # Parsing again should give same result
        req2 = Requirement(str(req))
        assert req.extras == req2.extras
        
    except InvalidRequirement:
        pass


@given(st.text(alphabet=string.ascii_letters + string.digits + ".-_", min_size=1, max_size=30))
def test_name_case_preservation(name):
    """Test that package name case is preserved exactly"""
    try:
        req = Requirement(name)
        # Name should be preserved exactly as input
        assert req.name == name, f"Name changed: {name} -> {req.name}"
        
        # After round-trip
        req2 = Requirement(str(req))
        assert req2.name == name, f"Name changed after round-trip: {name} -> {req2.name}"
        
    except InvalidRequirement:
        pass


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
       st.text(min_size=1, max_size=100))
def test_marker_preservation(name, marker_text):
    """Test that markers are preserved"""
    req_str = f"{name}; {marker_text}"
    
    try:
        req = Requirement(req_str)
        
        if req.marker:
            # Marker should exist
            assert str(req.marker) is not None
            
            # Round-trip should preserve marker
            req2 = Requirement(str(req))
            assert str(req.marker) == str(req2.marker)
            
    except InvalidRequirement:
        pass


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
       st.lists(st.sampled_from([">=", "<=", ">", "<", "==", "!=", "~=", "==="]), min_size=1, max_size=3),
       st.lists(st.text(alphabet=string.digits + ".", min_size=1, max_size=8), min_size=1, max_size=3))
def test_specifier_operator_handling(name, operators, versions):
    """Test that different operators are handled correctly"""
    specs = []
    for op, ver in zip(operators, versions):
        specs.append(f"{op}{ver}")
    
    req_str = f"{name}{','.join(specs)}"
    
    try:
        req = Requirement(req_str)
        
        # Should have all specifiers
        spec_str = str(req.specifier)
        
        # Round-trip should preserve
        req2 = Requirement(str(req))
        assert str(req2.specifier) == spec_str
        
    except InvalidRequirement:
        pass


@given(st.text(alphabet=string.ascii_letters + string.digits + ".-_", min_size=1, max_size=20))
def test_empty_specifier_handling(name):
    """Test handling of packages with no version specifier"""
    req_str = name
    
    try:
        req = Requirement(req_str)
        
        # Should have empty specifier
        assert str(req.specifier) == ""
        
        # Round-trip should preserve
        req2 = Requirement(str(req))
        assert str(req2.specifier) == ""
        
    except InvalidRequirement:
        pass


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
       st.text(alphabet=string.printable, min_size=1, max_size=200))
def test_url_with_fragment(name, url):
    """Test URL handling with fragments and special characters"""
    req_str = f"{name} @ {url}"
    
    try:
        req = Requirement(req_str)
        
        # URL should be set (though may be normalized)
        assert req.url is not None
        
        # Round-trip should work
        req2 = Requirement(str(req))
        assert req2.url == req.url
        
    except InvalidRequirement:
        pass


# Test the interaction between different components
@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
       st.lists(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=5), min_size=0, max_size=3),
       st.text(alphabet=string.digits + ".", min_size=0, max_size=10))
def test_combined_components(name, extras, version):
    """Test combinations of name, extras, and version"""
    # Build requirement with all components
    req_str = name
    if extras:
        req_str += f"[{','.join(extras)}]"
    if version:
        req_str += f"=={version}"
    
    try:
        req = Requirement(req_str)
        
        # Verify all components
        assert req.name == name
        
        if extras:
            assert all(e in req.extras for e in extras)
        else:
            assert len(req.extras) == 0
            
        # Round-trip
        req2 = Requirement(str(req))
        assert req2.name == req.name
        assert req2.extras == req.extras
        assert str(req2.specifier) == str(req.specifier)
        
    except InvalidRequirement:
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])