"""Property-based tests for Cython.Utils functions using Hypothesis"""

import re
from hypothesis import given, strategies as st, assume, settings
import Cython.Utils as Utils


# Test 1: strip_py2_long_suffix is idempotent
@given(st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1))
def test_strip_py2_long_suffix_idempotent(s):
    """Property: strip_py2_long_suffix(strip_py2_long_suffix(x)) == strip_py2_long_suffix(x)"""
    once = Utils.strip_py2_long_suffix(s)
    twice = Utils.strip_py2_long_suffix(once)
    assert once == twice, f"Not idempotent: {repr(s)} -> {repr(once)} -> {repr(twice)}"


# Test 2: strip_py2_long_suffix with valid Python 2 long literals
@given(st.one_of(
    st.from_regex(r'\d+[lL]', fullmatch=True),
    st.from_regex(r'0[xX][0-9a-fA-F]+[lL]', fullmatch=True),
    st.from_regex(r'0[oO][0-7]+[lL]', fullmatch=True),
    st.from_regex(r'0[bB][01]+[lL]', fullmatch=True),
))
def test_strip_py2_long_suffix_removes_suffix(s):
    """Property: For valid Python 2 long literals, the suffix should be removed"""
    result = Utils.strip_py2_long_suffix(s)
    assert not result.endswith('L') and not result.endswith('l')
    assert result == s[:-1]  # Should remove exactly one character


# Test 3: normalise_float_repr produces consistent output for equivalent representations
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_normalise_float_repr_consistent(f):
    """Property: Different string representations of the same float normalize to the same result"""
    # Create different representations
    repr1 = str(f)
    repr2 = f"{f:.10f}".rstrip('0')  # More decimal places
    
    result1 = Utils.normalise_float_repr(repr1)
    result2 = Utils.normalise_float_repr(repr2)
    
    # They should normalize to the same value
    # Convert back to float for comparison (accounting for representation differences)
    try:
        float1 = float(result1.rstrip('.'))
        float2 = float(result2.rstrip('.'))
        assert abs(float1 - float2) < 1e-10, f"Different results: {repr1} -> {result1}, {repr2} -> {result2}"
    except ValueError:
        # If conversion fails, at least check they're the same string
        assert result1 == result2


# Test 4: str_to_number correctly parses different integer bases
@given(st.integers(min_value=0, max_value=255))
def test_str_to_number_hex_parsing(n):
    """Property: str_to_number correctly parses hex literals"""
    hex_str = f"0x{n:X}"
    result = Utils.str_to_number(hex_str)
    assert result == n, f"Failed to parse {hex_str}: got {result}, expected {n}"


@given(st.integers(min_value=0, max_value=63))
def test_str_to_number_octal_parsing(n):
    """Property: str_to_number correctly parses octal literals"""
    octal_str = f"0o{n:o}"
    result = Utils.str_to_number(octal_str)
    assert result == n, f"Failed to parse {octal_str}: got {result}, expected {n}"


@given(st.integers(min_value=0, max_value=15))
def test_str_to_number_binary_parsing(n):
    """Property: str_to_number correctly parses binary literals"""
    binary_str = f"0b{n:b}"
    result = Utils.str_to_number(binary_str)
    assert result == n, f"Failed to parse {binary_str}: got {result}, expected {n}"


# Test 5: str_to_number round-trip property
@given(st.integers(min_value=-1000000, max_value=1000000))
def test_str_to_number_decimal_round_trip(n):
    """Property: str_to_number(str(n)) == n for decimal integers"""
    result = Utils.str_to_number(str(n))
    assert result == n, f"Round-trip failed: {n} -> {str(n)} -> {result}"


# Test 6: build_hex_version deterministic
@given(st.from_regex(r'\d+\.\d+\.\d+', fullmatch=True))
def test_build_hex_version_deterministic(version):
    """Property: build_hex_version is deterministic - same input always gives same output"""
    result1 = Utils.build_hex_version(version)
    result2 = Utils.build_hex_version(version)
    assert result1 == result2, f"Non-deterministic: {version} gave {result1} and {result2}"


# Test 7: build_hex_version with prerelease versions
@given(
    major=st.integers(min_value=0, max_value=99),
    minor=st.integers(min_value=0, max_value=99),
    patch=st.integers(min_value=0, max_value=99),
    prerelease=st.sampled_from(['a', 'b', 'rc']),
    prerelease_num=st.integers(min_value=1, max_value=9)
)
def test_build_hex_version_prerelease(major, minor, patch, prerelease, prerelease_num):
    """Property: build_hex_version handles prerelease versions consistently"""
    version = f"{major}.{minor}.{patch}{prerelease}{prerelease_num}"
    result = Utils.build_hex_version(version)
    
    # Check it returns an integer
    assert isinstance(result, int)
    
    # Check the hex format makes sense
    hex_str = f"{result:08X}"
    
    # The prerelease indicator should be in the result
    if prerelease == 'a':
        assert hex_str[-2] == 'A', f"Alpha version {version} should have A in hex: {hex_str}"
    elif prerelease == 'b':
        assert hex_str[-2] == 'B', f"Beta version {version} should have B in hex: {hex_str}"
    elif prerelease == 'rc':
        assert hex_str[-2] == 'C', f"RC version {version} should have C in hex: {hex_str}"


# Test 8: normalise_float_repr idempotence
@given(st.floats(allow_nan=False, min_value=-1e10, max_value=1e10))
def test_normalise_float_repr_idempotent(f):
    """Property: normalise_float_repr is idempotent"""
    s = str(f)
    once = Utils.normalise_float_repr(s)
    twice = Utils.normalise_float_repr(once)
    assert once == twice, f"Not idempotent: {s} -> {once} -> {twice}"


# Test 9: normalise_float_repr preserves special values
def test_normalise_float_repr_special_values():
    """Property: normalise_float_repr correctly handles special float values"""
    assert Utils.normalise_float_repr('inf') == 'inf.'
    assert Utils.normalise_float_repr('-inf') == '-inf.'
    assert Utils.normalise_float_repr('nan') == 'nan.'
    
    # Also test uppercase variants
    assert Utils.normalise_float_repr('INF') == 'inf.'
    assert Utils.normalise_float_repr('-INF') == '-inf.'
    assert Utils.normalise_float_repr('NAN') == 'nan.'


if __name__ == "__main__":
    # Run a quick test
    print("Running property-based tests for Cython.Utils...")
    test_strip_py2_long_suffix_idempotent()
    test_normalise_float_repr_special_values()
    print("Quick tests passed! Run with pytest for full testing.")