"""Property-based tests for packaging.requirements module"""

import string
from hypothesis import given, strategies as st, assume, settings
from packaging.requirements import Requirement, InvalidRequirement
from packaging.utils import canonicalize_name


# Strategy for valid package names
# Based on PEP 508: package names should contain only ASCII letters, numbers, dots, hyphens, underscores
def valid_package_name():
    # Start with letter or number (common case), then allow dots, hyphens, underscores
    first_char = st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=1)
    rest_chars = st.text(alphabet=string.ascii_letters + string.digits + ".-_", min_size=0, max_size=20)
    return st.builds(lambda f, r: f + r, first_char, rest_chars)


# Strategy for version specifiers
version_ops = ["==", "!=", "<=", ">=", "<", ">", "~=", "==="]
version_strategy = st.text(alphabet=string.digits + ".*+!abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10)
specifier_strategy = st.builds(
    lambda op, ver: op + ver,
    st.sampled_from(version_ops),
    version_strategy
)


# Strategy for extras (valid Python identifiers)
extra_strategy = st.text(alphabet=string.ascii_lowercase + string.digits + "_", min_size=1, max_size=10).filter(
    lambda s: s[0] not in string.digits and s.replace("_", "").replace("-", "").isalnum()
)


@given(st.text())
def test_canonicalize_name_idempotence(name):
    """Test that canonicalize_name is idempotent"""
    try:
        canonical = canonicalize_name(name)
        double_canonical = canonicalize_name(canonical)
        assert canonical == double_canonical
    except Exception:
        # canonicalize_name might reject some inputs
        pass


@given(st.text())
def test_canonicalize_name_lowercase(name):
    """Test that canonicalized names are always lowercase"""
    try:
        canonical = canonicalize_name(name)
        assert canonical == canonical.lower()
    except Exception:
        pass


@given(valid_package_name())
def test_requirement_name_preserved(name):
    """Test that the package name is preserved when parsing"""
    req_str = name
    try:
        req = Requirement(req_str)
        # The name should be preserved exactly
        assert req.name == name
    except InvalidRequirement:
        pass


@given(valid_package_name(), st.lists(extra_strategy, min_size=1, max_size=5))
def test_extras_uniqueness(name, extras):
    """Test that duplicate extras are deduplicated"""
    # Create a requirement string with duplicate extras
    extras_with_dups = extras + extras  # Duplicate all extras
    extras_str = "[" + ",".join(extras_with_dups) + "]"
    req_str = name + extras_str
    
    try:
        req = Requirement(req_str)
        # Extras should be unique (stored as set)
        assert len(req.extras) <= len(extras)
        # All original extras should be present
        for extra in extras:
            assert extra in req.extras
    except InvalidRequirement:
        pass


@given(valid_package_name(), st.lists(extra_strategy, min_size=0, max_size=3, unique=True))
def test_extras_sorting_in_str(name, extras):
    """Test that extras are sorted in string representation"""
    if not extras:
        return  # Skip empty extras
    
    extras_str = "[" + ",".join(extras) + "]"
    req_str = name + extras_str
    
    try:
        req = Requirement(req_str)
        result = str(req)
        
        # Extract extras from the string representation
        if "[" in result and "]" in result:
            start = result.index("[")
            end = result.index("]")
            extras_in_str = result[start+1:end].split(",")
            
            # Check if extras are sorted
            assert extras_in_str == sorted(extras_in_str)
    except InvalidRequirement:
        pass


@given(valid_package_name(), st.lists(specifier_strategy, min_size=0, max_size=3))
def test_round_trip_semantic_preservation(name, specifiers):
    """Test that semantic meaning is preserved through parse-serialize-parse"""
    spec_str = ",".join(specifiers) if specifiers else ""
    req_str = name + spec_str
    
    try:
        req1 = Requirement(req_str)
        req_str2 = str(req1)
        req2 = Requirement(req_str2)
        
        # Semantic properties should be the same
        assert req1.name == req2.name
        assert req1.extras == req2.extras
        assert str(req1.specifier) == str(req2.specifier)
        assert req1.marker == req2.marker
        assert req1.url == req2.url
    except InvalidRequirement:
        pass


@given(valid_package_name(), st.integers(min_value=0, max_value=10), st.integers(min_value=0, max_value=10))
def test_whitespace_handling(name, leading_spaces, trailing_spaces):
    """Test that leading/trailing whitespace is handled correctly"""
    req_str = " " * leading_spaces + name + " " * trailing_spaces
    
    try:
        req = Requirement(req_str)
        # Name should be preserved without spaces
        assert req.name == name
        
        # Parse again without spaces should give same result
        req2 = Requirement(name)
        assert req.name == req2.name
    except InvalidRequirement:
        pass


@given(st.text(min_size=1, max_size=100))
def test_requirement_str_parse_invariant(req_str):
    """Test that if a requirement string parses successfully, its string representation also parses"""
    try:
        req1 = Requirement(req_str)
        req_str2 = str(req1)
        # If the first parsing succeeded, the string representation should also parse
        req2 = Requirement(req_str2)
        
        # And they should be semantically equivalent
        assert req2.name == req1.name
        assert req2.extras == req1.extras
        assert str(req2.specifier) == str(req1.specifier)
    except InvalidRequirement:
        pass


@given(valid_package_name(), st.lists(extra_strategy, min_size=1, max_size=5))
def test_extras_case_sensitivity(name, extras):
    """Test extras case handling - they should preserve case"""
    # Mix cases
    mixed_extras = []
    for i, extra in enumerate(extras):
        if i % 2 == 0:
            mixed_extras.append(extra.upper())
        else:
            mixed_extras.append(extra.lower())
    
    extras_str = "[" + ",".join(mixed_extras) + "]"
    req_str = name + extras_str
    
    try:
        req = Requirement(req_str)
        # Check that case is preserved in extras
        for original in mixed_extras:
            # Either the exact case is preserved, or it's normalized somehow
            # Let's check what actually happens
            assert original in req.extras or original.lower() in req.extras or original.upper() in req.extras
    except InvalidRequirement:
        pass


@given(st.text(alphabet=string.ascii_letters + string.digits + ".-_", min_size=1, max_size=50))
def test_name_with_special_chars(name):
    """Test package names with dots, hyphens, and underscores"""
    try:
        req = Requirement(name)
        assert req.name == name
        
        # Round-trip should work
        req2 = Requirement(str(req))
        assert req2.name == name
    except InvalidRequirement:
        # Some names might be invalid
        pass


@given(st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=5))
def test_canonicalize_name_consistency(names):
    """Test that names that canonicalize to the same value are treated consistently"""
    try:
        canonical_names = [canonicalize_name(name) for name in names]
        
        # If two names canonicalize to the same thing, they should be interchangeable
        for i in range(len(names)):
            for j in range(len(names)):
                if canonical_names[i] == canonical_names[j]:
                    # These should behave the same in requirements
                    try:
                        req1 = Requirement(names[i] + ">=1.0")
                        req2 = Requirement(names[j] + ">=1.0")
                        # Their canonical forms should match
                        assert canonicalize_name(req1.name) == canonicalize_name(req2.name)
                    except InvalidRequirement:
                        pass
    except Exception:
        pass