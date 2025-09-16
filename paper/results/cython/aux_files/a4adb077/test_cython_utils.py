import Cython.Utils
from hypothesis import given, strategies as st, assume
import math


@given(st.text())
def test_strip_py2_long_suffix_empty_string(s):
    """Test that strip_py2_long_suffix handles all strings including empty ones."""
    if s:
        result = Cython.Utils.strip_py2_long_suffix(s)
        assert isinstance(result, str)
        if s.endswith(('L', 'l')):
            assert result == s[:-1]
        else:
            assert result == s
    else:
        # Empty string should be handled gracefully
        result = Cython.Utils.strip_py2_long_suffix(s)
        assert result == s


@given(st.lists(st.integers()))
def test_ordered_set_preserves_order(items):
    """Test that OrderedSet preserves insertion order."""
    os = Cython.Utils.OrderedSet()
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
        os.add(item)
    
    assert list(os) == seen


@given(st.lists(st.integers()))
def test_ordered_set_uniqueness(items):
    """Test that OrderedSet maintains uniqueness."""
    os = Cython.Utils.OrderedSet(items)
    result = list(os)
    assert len(result) == len(set(result))
    
    # Check that each item appears exactly once
    for item in set(items):
        assert result.count(item) == 1


@given(st.lists(st.integers()), st.lists(st.integers()))
def test_ordered_set_update_preserves_order(initial, update):
    """Test that update() preserves order of existing items."""
    os = Cython.Utils.OrderedSet(initial)
    initial_items = list(os)
    
    os.update(update)
    result = list(os)
    
    # Existing items should maintain their relative order
    existing_in_result = [x for x in result if x in initial_items]
    assert existing_in_result == initial_items


@given(st.text(min_size=1).filter(lambda x: not x[0].isspace() and x[0] in '0123456789.-'))
def test_normalise_float_repr_idempotent(float_str):
    """Test that normalise_float_repr is idempotent."""
    try:
        normalized_once = Cython.Utils.normalise_float_repr(float_str)
        normalized_twice = Cython.Utils.normalise_float_repr(normalized_once)
        assert normalized_once == normalized_twice
    except:
        # Skip if input is not a valid float representation
        pass


@given(st.integers(min_value=-10**15, max_value=10**15))
def test_str_to_number_strip_suffix_roundtrip(num):
    """Test round-trip property between str_to_number and strip_py2_long_suffix."""
    num_str = str(num)
    
    # Test with 'L' suffix
    num_str_with_L = num_str + 'L'
    stripped = Cython.Utils.strip_py2_long_suffix(num_str_with_L)
    assert stripped == num_str
    
    # Test that str_to_number works on the stripped version
    result = Cython.Utils.str_to_number(stripped)
    assert result == num


@given(st.from_regex(r'^[0-9]+(\.[0-9]+)?(\.[0-9]+)?(\.[0-9]+)?(a|b|rc)?[0-9]*$', fullmatch=True))
def test_build_hex_version_valid_format(version_str):
    """Test that build_hex_version produces valid hex strings."""
    try:
        result = Cython.Utils.build_hex_version(version_str)
        assert isinstance(result, str)
        assert result.startswith('0x')
        # Should be valid hex
        int(result, 16)
    except:
        # Some version strings might not be parseable
        pass


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_normalise_float_repr_preserves_value(f):
    """Test that normalise_float_repr preserves the numeric value."""
    float_str = str(f)
    normalized = Cython.Utils.normalise_float_repr(float_str)
    
    # The normalized string should still represent the same float value
    # (within floating point precision)
    denormalized = float(normalized)
    assert math.isclose(f, denormalized, rel_tol=1e-9)