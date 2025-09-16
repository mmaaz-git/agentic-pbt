import io
import sys
from hypothesis import given, strategies as st, settings, assume
import numpy as np
from tqdm.contrib import tenumerate, tmap, tzip, DummyTqdmFile


# Strategy for reasonable sized lists  
reasonable_lists = st.lists(st.integers(), min_size=0, max_size=100)


# Test tenumerate
@settings(max_examples=1000)
@given(reasonable_lists, st.integers(min_value=-1000, max_value=1000))
def test_tenumerate_matches_enumerate(lst, start):
    """tenumerate should produce the same output as enumerate for regular iterables"""
    result = list(tenumerate(lst, start=start))
    expected = list(enumerate(lst, start=start))
    assert result == expected


@given(st.lists(st.integers(), min_size=1, max_size=20))
def test_tenumerate_numpy_array(lst):
    """tenumerate should match np.ndenumerate for numpy arrays"""
    arr = np.array(lst)
    result = list(tenumerate(arr))
    expected = list(np.ndenumerate(arr))
    assert result == expected


@given(st.integers(min_value=1, max_value=5), 
       st.integers(min_value=1, max_value=5),
       st.integers(min_value=0, max_value=100))
def test_tenumerate_numpy_2d_ignores_start(rows, cols, start):
    """tenumerate ignores start parameter for numpy arrays - documenting this behavior"""
    # Create a uniform 2D array
    arr = np.zeros((rows, cols), dtype=int)
    # The start parameter is ignored for numpy arrays
    result_with_start = list(tenumerate(arr, start=start))
    result_no_start = list(tenumerate(arr))
    expected = list(np.ndenumerate(arr))
    assert result_with_start == expected
    assert result_no_start == expected
    assert result_with_start == result_no_start


# Test tmap
@settings(max_examples=1000) 
@given(reasonable_lists)
def test_tmap_matches_map_single_sequence(lst):
    """tmap should produce the same output as map for single sequences"""
    func = lambda x: x * 2 + 1
    result = list(tmap(func, lst))
    expected = list(map(func, lst))
    assert result == expected


@settings(max_examples=1000)
@given(reasonable_lists, reasonable_lists)
def test_tmap_matches_map_multiple_sequences(lst1, lst2):
    """tmap should produce the same output as map for multiple sequences"""
    func = lambda x, y: x + y
    result = list(tmap(func, lst1, lst2))
    expected = list(map(func, lst1, lst2))
    assert result == expected


@given(reasonable_lists, reasonable_lists, reasonable_lists)
def test_tmap_three_sequences(lst1, lst2, lst3):
    """tmap should work with three sequences like map"""
    func = lambda x, y, z: x + y + z
    result = list(tmap(func, lst1, lst2, lst3))
    expected = list(map(func, lst1, lst2, lst3))
    assert result == expected


# Test tzip
@given(reasonable_lists)
def test_tzip_single_iterable(lst):
    """tzip with single iterable should match zip"""
    result = list(tzip(lst))
    expected = list(zip(lst))
    assert result == expected


@settings(max_examples=1000)
@given(reasonable_lists, reasonable_lists)
def test_tzip_matches_zip(lst1, lst2):
    """tzip should produce the same output as zip"""
    result = list(tzip(lst1, lst2))
    expected = list(zip(lst1, lst2))
    assert result == expected


@given(reasonable_lists, reasonable_lists, reasonable_lists)
def test_tzip_three_iterables(lst1, lst2, lst3):
    """tzip should work with three iterables like zip"""
    result = list(tzip(lst1, lst2, lst3))
    expected = list(zip(lst1, lst2, lst3))
    assert result == expected


@given(st.lists(st.integers(), min_size=0, max_size=50),
       st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=50))
def test_tzip_different_lengths(lst1, lst2):
    """tzip should handle different length iterables like zip (stop at shortest)"""
    result = list(tzip(lst1, lst2))
    expected = list(zip(lst1, lst2))
    assert result == expected


# Test DummyTqdmFile
@given(st.text(min_size=0, max_size=1000))
def test_dummy_tqdm_file_preserves_content_no_newline(text):
    """DummyTqdmFile should preserve content when no newline"""
    assume('\n' not in text)
    
    output = io.StringIO()
    dummy = DummyTqdmFile(output)
    dummy.write(text)
    # Force flush by deleting (calls __del__)
    del dummy
    
    # The content should be preserved (written on __del__)
    assert output.getvalue() == text


@given(st.lists(st.text(min_size=0, max_size=100).filter(lambda x: '\n' not in x), 
                min_size=1, max_size=10))
def test_dummy_tqdm_file_with_newlines(text_parts):
    """DummyTqdmFile should handle text with newlines correctly"""
    output = io.StringIO()
    dummy = DummyTqdmFile(output)
    
    # Write parts with newlines between them
    full_text = '\n'.join(text_parts)
    dummy.write(full_text)
    
    # Force flush
    del dummy
    
    # Should preserve the full text
    assert output.getvalue() == full_text


@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=5))
def test_dummy_tqdm_file_multiple_writes(texts):
    """DummyTqdmFile should handle multiple writes correctly"""
    output = io.StringIO()
    dummy = DummyTqdmFile(output)
    
    expected = ""
    for text in texts:
        dummy.write(text)
        expected += text
    
    # Force flush
    del dummy
    
    # All text should be preserved
    assert output.getvalue() == expected


# Edge case: empty iterables
def test_empty_iterables():
    """All functions should handle empty iterables correctly"""
    assert list(tenumerate([])) == list(enumerate([]))
    assert list(tmap(lambda x: x, [])) == list(map(lambda x: x, []))
    assert list(tzip([])) == list(zip([]))
    assert list(tzip([], [])) == list(zip([], []))


# Test potential integer overflow with large start values
@given(st.lists(st.integers(), min_size=1, max_size=10),
       st.integers(min_value=sys.maxsize - 100, max_value=sys.maxsize))
def test_tenumerate_large_start_values(lst, start):
    """tenumerate should handle large start values like enumerate"""
    result = list(tenumerate(lst, start=start))
    expected = list(enumerate(lst, start=start))
    assert result == expected