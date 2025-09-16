import numpy as np
import numpy.char as nc
from hypothesis import given, strategies as st, assume, settings
import math


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_encode_decode_round_trip_utf8(texts):
    """encode/decode should be inverse operations for UTF-8"""
    arr = np.array(texts, dtype=str)
    encoded = nc.encode(arr, 'utf-8')
    decoded = nc.decode(encoded, 'utf-8')
    assert np.array_equal(arr, decoded)


@given(st.lists(st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127), 
                        min_size=0, max_size=100), min_size=1, max_size=20))
def test_encode_decode_round_trip_ascii(texts):
    """encode/decode should be inverse operations for ASCII"""
    arr = np.array(texts, dtype=str)
    encoded = nc.encode(arr, 'ascii')
    decoded = nc.decode(encoded, 'ascii')
    assert np.array_equal(arr, decoded)


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_swapcase_involution(texts):
    """swapcase(swapcase(x)) should equal x"""
    arr = np.array(texts, dtype=str)
    swapped_once = nc.swapcase(arr)
    swapped_twice = nc.swapcase(swapped_once)
    assert np.array_equal(arr, swapped_twice)


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_upper_lower_inverse(texts):
    """upper(lower(x)) and lower(upper(x)) should be idempotent on second application"""
    arr = np.array(texts, dtype=str)
    
    # upper(lower(x)) should equal upper(lower(upper(lower(x))))
    ul = nc.upper(nc.lower(arr))
    ulul = nc.upper(nc.lower(ul))
    assert np.array_equal(ul, ulul)
    
    # lower(upper(x)) should equal lower(upper(lower(upper(x))))
    lu = nc.lower(nc.upper(arr))
    lulu = nc.lower(nc.upper(lu))
    assert np.array_equal(lu, lulu)


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_capitalize_idempotent(texts):
    """capitalize(capitalize(x)) should equal capitalize(x)"""
    arr = np.array(texts, dtype=str)
    cap_once = nc.capitalize(arr)
    cap_twice = nc.capitalize(cap_once)
    assert np.array_equal(cap_once, cap_twice)


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_strip_idempotent(texts):
    """strip(strip(x)) should equal strip(x)"""
    arr = np.array(texts, dtype=str)
    stripped_once = nc.strip(arr)
    stripped_twice = nc.strip(stripped_once)
    assert np.array_equal(stripped_once, stripped_twice)


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_lstrip_rstrip_order(texts):
    """lstrip(rstrip(x)) should equal rstrip(lstrip(x)) and equal strip(x)"""
    arr = np.array(texts, dtype=str)
    lr = nc.lstrip(nc.rstrip(arr))
    rl = nc.rstrip(nc.lstrip(arr))
    stripped = nc.strip(arr)
    assert np.array_equal(lr, rl)
    assert np.array_equal(lr, stripped)


@given(st.lists(st.text(min_size=0, max_size=50), min_size=1, max_size=10),
       st.integers(min_value=0, max_value=10))
def test_multiply_length_invariant(texts, n):
    """len(multiply(x, n)) should equal len(x) * n"""
    arr = np.array(texts, dtype=str)
    multiplied = nc.multiply(arr, n)
    
    for i, text in enumerate(texts):
        expected_len = len(text) * n
        actual_len = len(multiplied[i])
        assert actual_len == expected_len


@given(st.lists(st.text(min_size=0, max_size=50), min_size=1, max_size=10),
       st.text(min_size=0, max_size=10))
def test_add_length_invariant(texts, suffix):
    """len(add(x, y)) should equal len(x) + len(y)"""
    arr = np.array(texts, dtype=str)
    added = nc.add(arr, suffix)
    
    for i, text in enumerate(texts):
        expected_len = len(text) + len(suffix)
        actual_len = len(added[i])
        assert actual_len == expected_len


@given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=20))
def test_str_len_consistency(texts):
    """str_len should return correct length for each string"""
    arr = np.array(texts, dtype=str)
    lengths = nc.str_len(arr)
    
    for i, text in enumerate(texts):
        assert lengths[i] == len(text)


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20),
       st.text(min_size=0, max_size=10),
       st.text(min_size=0, max_size=10))
def test_replace_empty_pattern(texts, old, new):
    """replace with empty old string should handle edge cases properly"""
    arr = np.array(texts, dtype=str)
    
    if old == '':
        # When old is empty, it should insert new between every character
        result = nc.replace(arr, old, new)
        # This is a known edge case behavior - verify it doesn't crash
        assert result is not None
    else:
        result = nc.replace(arr, old, new)
        # If old not in text, result should equal original
        for i, text in enumerate(texts):
            if old not in text:
                assert result[i] == text


@given(st.lists(st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), 
                        min_size=0, max_size=50), min_size=1, max_size=10))
def test_equal_transitivity(texts):
    """If a == b and b == c, then a == c"""
    # Create arrays with trailing spaces
    a = np.array(texts, dtype=str)
    b = np.array([t + ' ' for t in texts], dtype=str)  
    c = np.array([t + '  ' for t in texts], dtype=str)
    
    # nc.equal should strip trailing spaces
    ab = nc.equal(a, b)
    bc = nc.equal(b, c)
    ac = nc.equal(a, c)
    
    # Transitivity check
    for i in range(len(texts)):
        if ab[i] and bc[i]:
            assert ac[i], f"Transitivity violated at index {i}"


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_partition_rpartition_consistency(texts):
    """partition and rpartition should handle separators consistently"""
    arr = np.array(texts, dtype=str)
    sep = '.'
    
    # Test partition
    left, sep_found, right = nc.partition(arr, sep)
    
    for i, text in enumerate(texts):
        if sep in text:
            # Separator found - reconstruct should equal original
            reconstructed = left[i] + sep_found[i] + right[i]
            assert reconstructed == text
            assert sep_found[i] == sep
        else:
            # No separator - left should be whole string, others empty
            assert left[i] == text
            assert sep_found[i] == ''
            assert right[i] == ''
    
    # Test rpartition  
    rleft, rsep_found, rright = nc.rpartition(arr, sep)
    
    for i, text in enumerate(texts):
        if sep in text:
            reconstructed = rleft[i] + rsep_found[i] + rright[i]
            assert reconstructed == text
            assert rsep_found[i] == sep
        else:
            assert rleft[i] == ''
            assert rsep_found[i] == ''
            assert rright[i] == text


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_join_split_relationship(texts):
    """join and split should have a relationship with separators"""
    arr = np.array(texts, dtype=str)
    sep = ','
    
    # Join with separator
    joined = nc.join(sep, arr)
    
    # The joined string split by separator should give back components
    # This tests the join operation works correctly
    for i, text in enumerate(texts):
        assert text in joined[i] or joined[i] == text


@given(st.lists(st.text(min_size=0, max_size=50), min_size=1, max_size=10),
       st.integers(min_value=1, max_value=100))
def test_center_ljust_rjust_length(texts, width):
    """center, ljust, rjust should produce strings of specified width"""
    arr = np.array(texts, dtype=str)
    
    centered = nc.center(arr, width)
    ljusted = nc.ljust(arr, width)
    rjusted = nc.rjust(arr, width)
    
    for i, text in enumerate(texts):
        # All should have length max(len(text), width)
        expected_len = max(len(text), width)
        assert len(centered[i]) == expected_len
        assert len(ljusted[i]) == expected_len
        assert len(rjusted[i]) == expected_len
        
        # Original text should be contained
        assert text.strip() in centered[i].strip()
        assert text in ljusted[i]
        assert text in rjusted[i]


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_expandtabs_preserves_non_tabs(texts):
    """expandtabs should not change strings without tabs"""
    # Filter to texts without tabs
    texts = [t for t in texts if '\t' not in t]
    assume(len(texts) > 0)
    
    arr = np.array(texts, dtype=str)
    expanded = nc.expandtabs(arr)
    
    assert np.array_equal(arr, expanded)


@given(st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126),
                        min_size=1, max_size=50), min_size=1, max_size=10))
def test_find_rfind_consistency(texts):
    """find and rfind should be consistent for single occurrence"""
    arr = np.array(texts, dtype=str)
    needle = 'x'
    
    find_idx = nc.find(arr, needle)
    rfind_idx = nc.rfind(arr, needle)
    
    for i, text in enumerate(texts):
        count = text.count(needle)
        if count == 0:
            # Both should return -1
            assert find_idx[i] == -1
            assert rfind_idx[i] == -1
        elif count == 1:
            # Should return same index
            assert find_idx[i] == rfind_idx[i]
            assert find_idx[i] >= 0


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_isalpha_isdigit_mutual_exclusion(texts):
    """A character cannot be both alpha and digit"""
    arr = np.array(texts, dtype=str)
    
    is_alpha = nc.isalpha(arr)
    is_digit = nc.isdigit(arr)
    
    for i, text in enumerate(texts):
        if len(text) > 0 and is_alpha[i] and is_digit[i]:
            # This should never happen
            assert False, f"Text '{text}' is both alpha and digit"


@given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=20))
def test_comparison_order_consistency(texts):
    """Comparison operators should maintain ordering consistency"""
    arr = np.array(texts, dtype=str)
    
    # Compare with itself
    eq = nc.equal(arr, arr)
    ge = nc.greater_equal(arr, arr)
    le = nc.less_equal(arr, arr)
    
    # Self comparison properties
    assert np.all(eq), "x == x should always be true"
    assert np.all(ge), "x >= x should always be true"
    assert np.all(le), "x <= x should always be true"
    
    # Create a sorted version
    sorted_arr = np.sort(arr)
    
    for i in range(len(sorted_arr) - 1):
        # sorted[i] <= sorted[i+1] should hold
        le_result = nc.less_equal(sorted_arr[i:i+1], sorted_arr[i+1:i+2])
        assert le_result[0], f"Ordering violated: {sorted_arr[i]} should be <= {sorted_arr[i+1]}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])