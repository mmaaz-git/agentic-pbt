import re
from hypothesis import given, strategies as st, assume, settings
import packaging.utils
from packaging.version import Version
from packaging.utils import InvalidSdistFilename, InvalidWheelFilename, InvalidName


# Strategy for valid package names based on the validation regex
# The validate regex pattern is: ^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$
# This matches names that start and end with alphanumeric, with optional ._- in between
def valid_package_name_strategy():
    # Generate names that follow Python package naming conventions
    # Create a combined character set for middle chars
    alphanumeric = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    middle_chars_alphabet = alphanumeric + "._-"
    
    first_char = st.text(alphabet=alphanumeric, min_size=1, max_size=1)
    middle_chars = st.text(
        alphabet=middle_chars_alphabet,
        min_size=0,
        max_size=20
    )
    last_char = st.text(alphabet=alphanumeric, min_size=1, max_size=1)
    
    return st.builds(
        lambda f, m, l: f + m + l if m else f,
        first_char, middle_chars, last_char
    ).filter(lambda s: not re.search(r'[-_.]{2,}', s))  # Avoid multiple consecutive separators


# Test 1: canonicalize_name idempotence
@given(valid_package_name_strategy())
def test_canonicalize_name_idempotence(name):
    """canonicalize_name should be idempotent - applying it twice gives same result"""
    canonical_once = packaging.utils.canonicalize_name(name)
    canonical_twice = packaging.utils.canonicalize_name(canonical_once)
    assert canonical_once == canonical_twice


# Test 2: is_normalized_name consistency with canonicalize_name
@given(valid_package_name_strategy())
def test_normalized_name_consistency(name):
    """canonicalized names should always be normalized according to is_normalized_name"""
    canonical = packaging.utils.canonicalize_name(name)
    # The canonical form should be normalized
    assert packaging.utils.is_normalized_name(canonical), f"Canonical name {canonical!r} is not normalized"


# Test 3: Normalized names should remain unchanged by canonicalization
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=30))
def test_normalized_names_unchanged(name):
    """If a name is already normalized, canonicalization shouldn't change it"""
    # Filter to only test valid normalized names
    if packaging.utils.is_normalized_name(name):
        canonical = packaging.utils.canonicalize_name(name)
        assert canonical == name


# Test 4: parse_sdist_filename round-trip
@given(
    valid_package_name_strategy(),
    st.text(alphabet="0123456789.", min_size=1, max_size=20).filter(
        lambda v: re.match(r'^\d+(\.\d+)*$', v) is not None
    )
)
def test_parse_sdist_filename_roundtrip(name, version_str):
    """Creating and parsing an sdist filename should preserve normalized name and version"""
    try:
        version = Version(version_str)
    except:
        assume(False)
    
    # Create sdist filename
    canonical_name = packaging.utils.canonicalize_name(name)
    filename = f"{name}-{version_str}.tar.gz"
    
    # Try to parse it
    try:
        parsed_name, parsed_version = packaging.utils.parse_sdist_filename(filename)
        # The parsed name should be the canonicalized version
        assert parsed_name == canonical_name
        assert parsed_version == version
    except InvalidSdistFilename:
        # This might happen if the name contains characters that make an invalid filename
        pass


# Test 5: parse_wheel_filename basic validation
@given(
    valid_package_name_strategy(),
    st.text(alphabet="0123456789.", min_size=1, max_size=20).filter(
        lambda v: re.match(r'^\d+(\.\d+)*$', v) is not None
    )
)
def test_parse_wheel_filename_basic(name, version_str):
    """Creating and parsing a wheel filename should preserve normalized name and version"""
    try:
        version = Version(version_str)
    except:
        assume(False)
    
    # Only use names that don't contain __ and match the wheel name pattern
    assume("__" not in name)
    assume(re.match(r"^[\w\d._]*$", name, re.UNICODE) is not None)
    
    canonical_name = packaging.utils.canonicalize_name(name)
    # Create a minimal valid wheel filename
    filename = f"{name}-{version_str}-py3-none-any.whl"
    
    try:
        parsed_name, parsed_version, build, tags = packaging.utils.parse_wheel_filename(filename)
        assert parsed_name == canonical_name
        assert parsed_version == version
        assert build == ()  # No build tag in our test
    except InvalidWheelFilename:
        pass


# Test 6: canonicalize_version idempotence with Version objects
@given(st.text(alphabet="0123456789.", min_size=1, max_size=20))
def test_canonicalize_version_idempotence(version_str):
    """canonicalize_version should be idempotent"""
    try:
        # First canonicalization
        canonical_once = packaging.utils.canonicalize_version(version_str)
        # Second canonicalization
        canonical_twice = packaging.utils.canonicalize_version(canonical_once)
        assert canonical_once == canonical_twice
    except:
        # If it's not a valid version, it should still be idempotent
        canonical_once = packaging.utils.canonicalize_version(version_str)
        canonical_twice = packaging.utils.canonicalize_version(canonical_once)
        assert canonical_once == canonical_twice


# Test 7: Test the strip_trailing_zero behavior documented in canonicalize_version
@given(st.integers(min_value=0, max_value=100), st.integers(min_value=0, max_value=100))
def test_canonicalize_version_trailing_zeros(major, minor):
    """Test trailing zero stripping behavior as documented"""
    version_str = f"{major}.{minor}.0"
    
    # With strip_trailing_zero=True (default)
    canonical_stripped = packaging.utils.canonicalize_version(version_str)
    # With strip_trailing_zero=False
    canonical_not_stripped = packaging.utils.canonicalize_version(version_str, strip_trailing_zero=False)
    
    # The not-stripped version should keep the trailing zero
    if version_str == "0.0.0":
        assert canonical_stripped == "0"
        assert canonical_not_stripped == "0.0.0"
    elif minor == 0 and major != 0:
        assert canonical_stripped == str(major)
        assert canonical_not_stripped == version_str
    elif minor != 0:
        assert canonical_stripped == f"{major}.{minor}"
        assert canonical_not_stripped == version_str


# Test 8: Test case sensitivity in canonicalize_name
@given(st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20))
def test_canonicalize_name_case_insensitive(name):
    """canonicalize_name should produce same result regardless of case"""
    canonical_lower = packaging.utils.canonicalize_name(name.lower())
    canonical_upper = packaging.utils.canonicalize_name(name.upper())
    canonical_mixed = packaging.utils.canonicalize_name(name)
    
    assert canonical_lower == canonical_upper == canonical_mixed


# Test 9: Test that certain characters are all normalized to dash
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=5),
    st.sampled_from(['_', '.', '-']),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=5)
)
def test_canonicalize_name_separator_normalization(prefix, separator, suffix):
    """All separators (-, _, .) should be normalized to dash"""
    name_dash = f"{prefix}-{suffix}"
    name_underscore = f"{prefix}_{suffix}"
    name_dot = f"{prefix}.{suffix}"
    
    canonical_dash = packaging.utils.canonicalize_name(name_dash)
    canonical_underscore = packaging.utils.canonicalize_name(name_underscore)
    canonical_dot = packaging.utils.canonicalize_name(name_dot)
    
    # All should produce the same canonical form
    assert canonical_dash == canonical_underscore == canonical_dot
    assert canonical_dash == f"{prefix}-{suffix}"


# Test 10: Multiple consecutive separators should collapse to single dash
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=5),
    st.integers(min_value=2, max_value=5),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=5)
)
def test_canonicalize_name_multiple_separators(prefix, sep_count, suffix):
    """Multiple consecutive separators should collapse to single dash"""
    separators = "_" * sep_count
    name = f"{prefix}{separators}{suffix}"
    canonical = packaging.utils.canonicalize_name(name)
    
    # Should have exactly one dash between prefix and suffix
    assert canonical == f"{prefix}-{suffix}"


# Test 11: is_normalized_name should reject consecutive dashes
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=5),
    st.integers(min_value=2, max_value=5),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=5)
)
def test_is_normalized_name_rejects_double_dash(prefix, dash_count, suffix):
    """is_normalized_name should reject names with consecutive dashes"""
    name = f"{prefix}{'-' * dash_count}{suffix}"
    assert not packaging.utils.is_normalized_name(name)


# Test 12: Testing invalid sdist filenames
@given(st.text(min_size=1, max_size=50))
def test_parse_sdist_filename_invalid_extensions(filename):
    """parse_sdist_filename should only accept .tar.gz or .zip extensions"""
    assume(not filename.endswith('.tar.gz'))
    assume(not filename.endswith('.zip'))
    
    try:
        packaging.utils.parse_sdist_filename(filename)
        assert False, f"Should have raised InvalidSdistFilename for {filename}"
    except InvalidSdistFilename:
        pass  # Expected


# Test 13: Testing parse_tag function
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=10),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=10),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=10)
)
def test_parse_tag_format(python_tag, abi_tag, platform_tag):
    """parse_tag should handle standard tag format"""
    tag_str = f"{python_tag}-{abi_tag}-{platform_tag}"
    tags = packaging.utils.parse_tag(tag_str)
    
    # Should return a frozenset
    assert isinstance(tags, frozenset)
    # Should have at least one tag
    assert len(tags) >= 1
    
    # Each tag should have the components
    for tag in tags:
        assert hasattr(tag, 'interpreter')
        assert hasattr(tag, 'abi') 
        assert hasattr(tag, 'platform')