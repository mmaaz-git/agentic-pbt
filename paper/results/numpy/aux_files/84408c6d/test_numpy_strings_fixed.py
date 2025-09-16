import numpy as np
import numpy.strings as ns
from hypothesis import given, strategies as st, assume, settings
import math
import pytest


def make_string_array(strings):
    """Convert list of strings to proper numpy string array"""
    if not strings:
        return np.array([], dtype='U')
    max_len = max(len(s) for s in strings)
    # Add some buffer for operations that might increase length
    dtype_len = max(max_len + 10, 1)
    return np.array(strings, dtype=f'U{dtype_len}')


@given(st.lists(st.text(min_size=0, max_size=50), min_size=1, max_size=10))
def test_encode_decode_round_trip(strings):
    """Test that decode(encode(x)) == x for UTF-8 encoding"""
    arr = make_string_array(strings)
    encoded = ns.encode(arr, 'utf-8')
    decoded = ns.decode(encoded, 'utf-8')
    
    # Need to compare with same dtype
    expected = make_string_array(strings)
    assert np.array_equal(decoded, expected), f"Round-trip failed for {strings}"


@given(st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10),
       st.integers(min_value=-100, max_value=100))
def test_multiply_properties(strings, n):
    """Test properties of string multiplication"""
    arr = make_string_array(strings)
    
    # Need larger buffer for multiply operation
    if n > 0:
        max_len = max(len(s) for s in strings) if strings else 0
        dtype_len = max(max_len * n + 10, 1)
        arr = np.array(strings, dtype=f'U{dtype_len}')
    
    result = ns.multiply(arr, n)
    
    # Property 1: multiply by 0 or negative gives empty strings
    if n <= 0:
        for res in result:
            assert res == '', f"multiply({strings}, {n}) should give empty strings, got {res}"
    
    # Property 2: multiply by 1 gives original
    if n == 1:
        expected = make_string_array(strings)
        assert np.array_equal(result, expected), f"multiply by 1 should return original"
    
    # Property 3: length relationship
    if n > 0:
        for orig, res in zip(strings, result):
            assert len(res) == len(orig) * n, f"Length mismatch for multiply({orig}, {n})"


@given(st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10),
       st.text(min_size=1, max_size=5))
def test_partition_properties(strings, sep):
    """Test properties of partition function"""
    arr = make_string_array(strings)
    sep_arr = np.array(sep, dtype='U10')
    
    left, mid, right = ns.partition(arr, sep_arr)
    
    for i, s in enumerate(strings):
        l, m, r = str(left[i]), str(mid[i]), str(right[i])
        
        # Property 1: Reconstruction
        if m == sep:
            # If separator was found, reconstruction should work
            assert l + m + r == s, f"partition({s}, {sep}) doesn't reconstruct: {l}+{m}+{r} != {s}"
        else:
            # If separator not found, left should be whole string
            assert l == s and m == '' and r == '', f"partition({s}, {sep}) without match failed"
        
        # Property 2: Middle is either sep or empty
        assert m == sep or m == '', f"Middle part should be sep or empty, got {m}"


@given(st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10),
       st.text(min_size=1, max_size=5))
def test_rpartition_properties(strings, sep):
    """Test properties of rpartition function"""
    arr = make_string_array(strings)
    sep_arr = np.array(sep, dtype='U10')
    
    left, mid, right = ns.rpartition(arr, sep_arr)
    
    for i, s in enumerate(strings):
        l, m, r = str(left[i]), str(mid[i]), str(right[i])
        
        # Property 1: Reconstruction
        if m == sep:
            # If separator was found, reconstruction should work
            assert l + m + r == s, f"rpartition({s}, {sep}) doesn't reconstruct"
        else:
            # If separator not found, right should be whole string
            assert l == '' and m == '' and r == s, f"rpartition({s}, {sep}) without match failed"
        
        # Property 2: Middle is either sep or empty
        assert m == sep or m == '', f"Middle part should be sep or empty"


@given(st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), 
                       min_size=0, max_size=20), min_size=1, max_size=10),
       st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), 
              min_size=1, max_size=3),
       st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), 
              min_size=0, max_size=3),
       st.integers(min_value=-1, max_value=10))
def test_replace_count_property(strings, old, new, count):
    """Test replace with count parameter"""
    # Calculate max possible length after replacements
    max_expansions = max(s.count(old) for s in strings) if strings and old else 0
    expansion_factor = max(len(new) // max(len(old), 1), 1) if old else 1
    max_len = max(len(s) for s in strings) if strings else 0
    dtype_len = max(max_len * expansion_factor + max_expansions * len(new) + 10, 1)
    
    arr = np.array(strings, dtype=f'U{dtype_len}')
    old_arr = np.array(old, dtype='U10')
    new_arr = np.array(new, dtype='U10')
    
    result = ns.replace(arr, old_arr, new_arr, count=count)
    
    for orig, res in zip(strings, result):
        res = str(res)
        if count == 0:
            # count=0 should not replace anything
            assert res == orig, f"replace with count=0 should not change string"
        elif count == -1:
            # count=-1 should replace all occurrences
            if old and old != new:
                assert old not in res, f"replace with count=-1 should replace all"
        elif count > 0 and old:
            # Should replace at most 'count' occurrences
            orig_count = orig.count(old)
            if new != old and old not in new:
                replaced = min(count, orig_count)
                remaining = orig_count - replaced
                assert res.count(old) == remaining, f"Wrong number of replacements"


@given(st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10),
       st.text(min_size=1, max_size=5))
def test_count_substring(strings, sub):
    """Test count function properties"""
    arr = make_string_array(strings)
    sub_arr = np.array(sub, dtype='U10')
    
    counts = ns.count(arr, sub_arr)
    
    for s, c in zip(strings, counts):
        # Verify count matches Python's string count
        expected = s.count(sub)
        assert c == expected, f"count({s}, {sub}) = {c}, expected {expected}"


@given(st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10))
def test_case_functions_round_trip(strings):
    """Test case conversion functions"""
    arr = make_string_array(strings)
    
    # Test upper/lower round trip
    upper = ns.upper(arr)
    lower = ns.lower(upper)
    upper2 = ns.upper(lower)
    
    # After upper->lower->upper, should be same as first upper
    assert np.array_equal(upper, upper2), "upper->lower->upper should be idempotent"
    
    # Test swapcase twice returns original (for ASCII)
    ascii_strings = [s for s in strings if all(ord(c) < 128 for c in s) if s]
    if ascii_strings:
        ascii_arr = make_string_array(ascii_strings)
        swapped = ns.swapcase(ascii_arr)
        double_swapped = ns.swapcase(swapped)
        assert np.array_equal(ascii_arr, double_swapped), "swapcase twice should return original for ASCII"


@given(st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126),
                       min_size=0, max_size=20), min_size=1, max_size=10))
def test_strip_functions(strings):
    """Test strip, lstrip, rstrip consistency"""
    arr = make_string_array(strings)
    
    stripped = ns.strip(arr)
    lstripped = ns.lstrip(arr)
    rstripped = ns.rstrip(arr)
    
    for orig, s, l, r in zip(strings, stripped, lstripped, rstripped):
        s, l, r = str(s), str(l), str(r)
        # strip should be same as doing both lstrip and rstrip
        both = orig.lstrip().rstrip()
        assert s == both, f"strip({orig}) != lstrip().rstrip()"
        
        # Verify individual operations
        assert l == orig.lstrip(), f"lstrip mismatch"
        assert r == orig.rstrip(), f"rstrip mismatch"


@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10),
       st.text(min_size=1, max_size=3))
def test_partition_rpartition_single_occurrence(strings, sep):
    """Test relationship between partition and rpartition for single occurrence"""
    # Filter to strings that contain sep exactly once
    single_occurrence = [s for s in strings if s.count(sep) == 1]
    
    if single_occurrence:
        arr = make_string_array(single_occurrence)
        sep_arr = np.array(sep, dtype='U10')
        
        p_left, p_mid, p_right = ns.partition(arr, sep_arr)
        r_left, r_mid, r_right = ns.rpartition(arr, sep_arr)
        
        for i in range(len(single_occurrence)):
            # For single occurrence, partition and rpartition should give same result
            assert str(p_left[i]) == str(r_left[i]), "left parts should match for single occurrence"
            assert str(p_mid[i]) == str(r_mid[i]), "mid parts should match for single occurrence"
            assert str(p_right[i]) == str(r_right[i]), "right parts should match for single occurrence"


@given(st.lists(st.text(alphabet=st.sampled_from('0123456789+-'),
                       min_size=0, max_size=20), min_size=1, max_size=10),
       st.integers(min_value=0, max_value=100))
def test_zfill_properties(strings, width):
    """Test zfill function properties"""
    # Need larger buffer for zfill
    dtype_len = max(width + 10, max(len(s) for s in strings) if strings else 1, 1)
    arr = np.array(strings, dtype=f'U{dtype_len}')
    
    result = ns.zfill(arr, width)
    
    for orig, res in zip(strings, result):
        res = str(res)
        # Length should be at least width
        assert len(res) >= min(width, len(orig)), f"zfill result too short"
        
        # Should preserve sign if present
        if orig.startswith('-') or orig.startswith('+'):
            assert res[0] == orig[0], "Sign should be preserved"
            # Zeros should come after sign
            if len(res) > len(orig):
                assert '0' in res[1:len(res)-len(orig)+2], "Should have zeros after sign"
        
        # Result should end with original content (minus sign if present)
        if orig.startswith('-') or orig.startswith('+'):
            assert res.endswith(orig[1:]) or orig == res, "Content should be preserved"
        else:
            assert res.endswith(orig) or orig == res, "Content should be preserved"


@given(st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10),
       st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10))
def test_add_concatenation(strings1, strings2):
    """Test string addition (concatenation)"""
    # Make arrays same length
    min_len = min(len(strings1), len(strings2))
    if min_len == 0:
        return
        
    s1 = strings1[:min_len]
    s2 = strings2[:min_len]
    
    # Calculate required dtype size
    max_len = max(len(a) + len(b) for a, b in zip(s1, s2)) if s1 else 0
    dtype_len = max(max_len + 10, 1)
    
    arr1 = np.array(s1, dtype=f'U{dtype_len}')
    arr2 = np.array(s2, dtype=f'U{dtype_len}')
    
    result = ns.add(arr1, arr2)
    
    for str1, str2, res in zip(s1, s2, result):
        assert str(res) == str1 + str2, f"add({str1}, {str2}) should equal {str1 + str2}, got {res}"


@given(st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10),
       st.text(min_size=1, max_size=3))  
def test_find_rfind_consistency(strings, sub):
    """Test that find and rfind are consistent for single occurrence"""
    # Filter to strings with exactly one occurrence
    single = [s for s in strings if s.count(sub) == 1]
    
    if single:
        arr = make_string_array(single)
        sub_arr = np.array(sub, dtype='U10')
        
        find_results = ns.find(arr, sub_arr)
        rfind_results = ns.rfind(arr, sub_arr)
        
        # For single occurrence, find and rfind should give same position
        assert np.array_equal(find_results, rfind_results), "find and rfind should match for single occurrence"


@given(st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10))
def test_str_len_property(strings):
    """Test that str_len returns correct lengths"""
    arr = make_string_array(strings)
    lengths = ns.str_len(arr)
    
    for s, length in zip(strings, lengths):
        assert length == len(s), f"str_len({s}) = {length}, expected {len(s)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])