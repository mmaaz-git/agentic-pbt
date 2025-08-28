import numpy as np
import numpy.strings as ns
from hypothesis import given, strategies as st, assume, settings
import math
import pytest


@given(st.lists(st.text(min_size=0), min_size=1, max_size=10))
def test_encode_decode_round_trip(strings):
    """Test that decode(encode(x)) == x for UTF-8 encoding"""
    arr = np.array(strings, dtype=object)
    encoded = ns.encode(arr, 'utf-8')
    decoded = ns.decode(encoded, 'utf-8')
    assert np.array_equal(arr, decoded), f"Round-trip failed for {strings}"


@given(st.lists(st.text(min_size=0), min_size=1, max_size=10),
       st.integers(min_value=-100, max_value=100))
def test_multiply_properties(strings, n):
    """Test properties of string multiplication"""
    arr = np.array(strings, dtype=object)
    result = ns.multiply(arr, n)
    
    # Property 1: multiply by 0 or negative gives empty strings
    if n <= 0:
        assert all(s == '' for s in result), f"multiply({strings}, {n}) should give empty strings"
    
    # Property 2: multiply by 1 gives original
    if n == 1:
        assert np.array_equal(result, arr), f"multiply by 1 should return original"
    
    # Property 3: length relationship
    if n > 0:
        for orig, res in zip(arr, result):
            assert len(res) == len(orig) * n, f"Length mismatch for multiply({orig}, {n})"


@given(st.lists(st.text(min_size=0), min_size=1, max_size=10),
       st.text(min_size=1, max_size=5))
def test_partition_properties(strings, sep):
    """Test properties of partition function"""
    arr = np.array(strings, dtype=object)
    left, mid, right = ns.partition(arr, sep)
    
    for i, s in enumerate(arr):
        l, m, r = left[i], mid[i], right[i]
        
        # Property 1: Reconstruction
        if m == sep:
            # If separator was found, reconstruction should work
            assert l + m + r == s, f"partition({s}, {sep}) doesn't reconstruct"
        else:
            # If separator not found, left should be whole string
            assert l == s and m == '' and r == '', f"partition({s}, {sep}) without match failed"
        
        # Property 2: Middle is either sep or empty
        assert m == sep or m == '', f"Middle part should be sep or empty"


@given(st.lists(st.text(min_size=0), min_size=1, max_size=10),
       st.text(min_size=1, max_size=5))
def test_rpartition_properties(strings, sep):
    """Test properties of rpartition function"""
    arr = np.array(strings, dtype=object)
    left, mid, right = ns.rpartition(arr, sep)
    
    for i, s in enumerate(arr):
        l, m, r = left[i], mid[i], right[i]
        
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
    arr = np.array(strings, dtype=object)
    result = ns.replace(arr, old, new, count=count)
    
    for orig, res in zip(arr, result):
        if count == 0:
            # count=0 should not replace anything
            assert res == orig, f"replace with count=0 should not change string"
        elif count == -1:
            # count=-1 should replace all occurrences
            assert old not in res or new == old, f"replace with count=-1 should replace all"
        elif count > 0:
            # Should replace at most 'count' occurrences
            orig_count = orig.count(old)
            if new != old and old in new:
                # Complex case where new contains old - skip verification
                pass
            elif new == old:
                assert res == orig, "Replacing with same string should not change"
            else:
                # Count remaining occurrences
                replaced = min(count, orig_count)
                remaining = orig_count - replaced
                if old not in new:
                    assert res.count(old) == remaining, f"Wrong number of replacements"


@given(st.lists(st.text(min_size=0), min_size=1, max_size=10),
       st.text(min_size=1, max_size=5))
def test_count_substring(strings, sub):
    """Test count function properties"""
    arr = np.array(strings, dtype=object)
    counts = ns.count(arr, sub)
    
    for s, c in zip(arr, counts):
        # Verify count matches Python's string count
        expected = s.count(sub)
        assert c == expected, f"count({s}, {sub}) = {c}, expected {expected}"


@given(st.lists(st.text(min_size=0), min_size=1, max_size=10),
       st.lists(st.text(min_size=0), min_size=1, max_size=10))
def test_add_concatenation(strings1, strings2):
    """Test string addition (concatenation)"""
    # Make arrays same length
    min_len = min(len(strings1), len(strings2))
    arr1 = np.array(strings1[:min_len], dtype=object)
    arr2 = np.array(strings2[:min_len], dtype=object)
    
    result = ns.add(arr1, arr2)
    
    for s1, s2, res in zip(arr1, arr2, result):
        assert res == s1 + s2, f"add({s1}, {s2}) should equal {s1 + s2}"


@given(st.lists(st.text(min_size=0), min_size=1, max_size=10))
def test_case_functions_round_trip(strings):
    """Test case conversion functions"""
    arr = np.array(strings, dtype=object)
    
    # Test upper/lower round trip
    upper = ns.upper(arr)
    lower = ns.lower(upper)
    upper2 = ns.upper(lower)
    
    # After upper->lower->upper, should be same as first upper
    assert np.array_equal(upper, upper2), "upper->lower->upper should be idempotent"
    
    # Test swapcase twice returns original (for ASCII)
    ascii_strings = [s for s in strings if all(ord(c) < 128 for c in s)]
    if ascii_strings:
        ascii_arr = np.array(ascii_strings, dtype=object)
        swapped = ns.swapcase(ascii_arr)
        double_swapped = ns.swapcase(swapped)
        assert np.array_equal(ascii_arr, double_swapped), "swapcase twice should return original for ASCII"


@given(st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126),
                       min_size=0, max_size=20), min_size=1, max_size=10))
def test_strip_functions(strings):
    """Test strip, lstrip, rstrip consistency"""
    arr = np.array(strings, dtype=object)
    
    stripped = ns.strip(arr)
    lstripped = ns.lstrip(arr)
    rstripped = ns.rstrip(arr)
    
    for orig, s, l, r in zip(arr, stripped, lstripped, rstripped):
        # strip should be same as doing both lstrip and rstrip
        both = orig.lstrip().rstrip()
        assert s == both, f"strip({orig}) != lstrip().rstrip()"
        
        # Verify individual operations
        assert l == orig.lstrip(), f"lstrip mismatch"
        assert r == orig.rstrip(), f"rstrip mismatch"


@given(st.lists(st.text(min_size=1), min_size=1, max_size=10),
       st.text(min_size=1, max_size=3))
def test_partition_rpartition_consistency(strings, sep):
    """Test relationship between partition and rpartition"""
    arr = np.array(strings, dtype=object)
    
    p_left, p_mid, p_right = ns.partition(arr, sep)
    r_left, r_mid, r_right = ns.rpartition(arr, sep)
    
    for i, s in enumerate(arr):
        if sep in s:
            # Both should find the separator
            assert p_mid[i] == sep, "partition should find sep"
            assert r_mid[i] == sep, "rpartition should find sep"
            
            # For strings with single occurrence, results differ only in which side gets which part
            if s.count(sep) == 1:
                assert p_left[i] + p_mid[i] + p_right[i] == s
                assert r_left[i] + r_mid[i] + r_right[i] == s
                assert p_left[i] == r_left[i]
                assert p_right[i] == r_right[i]


@given(st.lists(st.text(alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Lt', 'Nd']),
                       min_size=0, max_size=20), min_size=1, max_size=10),
       st.integers(min_value=0, max_value=100))
def test_zfill_properties(strings, width):
    """Test zfill function properties"""
    arr = np.array(strings, dtype=object)
    result = ns.zfill(arr, width)
    
    for orig, res in zip(arr, result):
        # Length should be at least width
        assert len(res) >= width or len(res) == len(orig), f"zfill result too short"
        
        # Should preserve sign if present
        if orig.startswith('-') or orig.startswith('+'):
            assert res[0] == orig[0], "Sign should be preserved"
            # Zeros should come after sign
            if len(res) > len(orig):
                assert res[1] == '0', "Zeros should come after sign"
        
        # Result should end with original content (minus sign)
        if orig.startswith('-') or orig.startswith('+'):
            assert res.endswith(orig[1:]), "Content should be preserved"
        else:
            assert res.endswith(orig), "Content should be preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])