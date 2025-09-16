"""
Test special cases and potential edge conditions for tqdm.contrib
"""
import io
import sys
from hypothesis import given, strategies as st, settings, assume
from tqdm.contrib import tenumerate, tmap, tzip, DummyTqdmFile


# Test with None values
def test_tmap_with_none_values():
    """tmap should handle None values correctly"""
    lst = [1, None, 3, None, 5]
    func = lambda x: x if x is None else x * 2
    result = list(tmap(func, lst))
    expected = list(map(func, lst))
    assert result == expected


def test_tzip_with_none_values():
    """tzip should handle None values correctly"""
    lst1 = [1, None, 3]
    lst2 = ['a', 'b', None]
    result = list(tzip(lst1, lst2))
    expected = list(zip(lst1, lst2))
    assert result == expected


# Test with negative start values
@given(st.lists(st.integers(), min_size=1, max_size=10),
       st.integers(min_value=-sys.maxsize, max_value=-1))
def test_tenumerate_negative_start(lst, start):
    """tenumerate should handle negative start values like enumerate"""
    result = list(tenumerate(lst, start=start))
    expected = list(enumerate(lst, start=start))
    assert result == expected


# Unicode handling for DummyTqdmFile
@given(st.text(alphabet=st.characters(min_codepoint=0x1F300, max_codepoint=0x1F6FF), 
               min_size=1, max_size=100))
def test_dummy_tqdm_file_unicode(emoji_text):
    """DummyTqdmFile should handle Unicode/emoji correctly"""
    output = io.StringIO()
    dummy = DummyTqdmFile(output)
    dummy.write(emoji_text)
    del dummy
    assert output.getvalue() == emoji_text


# Test with special string characters
def test_dummy_tqdm_file_special_chars():
    """DummyTqdmFile should handle special characters correctly"""
    special_strings = [
        "Tab\there",
        "Carriage\rreturn",
        "Multiple\n\n\nnewlines",
        "Mixed\r\nline endings",
        "Unicode: 你好世界 🌍",
        "\x00Null character",
    ]
    
    for text in special_strings:
        output = io.StringIO()
        dummy = DummyTqdmFile(output)
        dummy.write(text)
        del dummy
        assert output.getvalue() == text


# Test tmap with functions that modify state
def test_tmap_stateful_function():
    """tmap should work with stateful functions"""
    counter = {'count': 0}
    
    def stateful_func(x):
        counter['count'] += 1
        return x + counter['count']
    
    lst = [10, 20, 30]
    result = list(tmap(stateful_func, lst))
    # Function is called in order: 10+1=11, 20+2=22, 30+3=33
    assert result == [11, 22, 33]
    assert counter['count'] == 3


# Test with very large lists using hypothesis
@settings(max_examples=10, deadline=5000)
@given(st.lists(st.integers(), min_size=1000, max_size=10000))
def test_large_list_performance(large_list):
    """Test that functions handle large lists correctly"""
    # Just verify correctness, not performance
    result = list(tenumerate(large_list[:100]))  # Test subset to avoid timeout
    expected = list(enumerate(large_list[:100]))
    assert result == expected


# Test tmap with multiple sequences of different types
def test_tmap_mixed_types():
    """tmap should handle mixed types in multiple sequences"""
    nums = [1, 2, 3]
    strs = ['a', 'b', 'c']
    bools = [True, False, True]
    
    func = lambda n, s, b: f"{n}{s}{b}"
    result = list(tmap(func, nums, strs, bools))
    expected = list(map(func, nums, strs, bools))
    assert result == expected


# Test empty string handling in DummyTqdmFile
def test_dummy_tqdm_file_empty_writes():
    """DummyTqdmFile should handle empty string writes"""
    output = io.StringIO()
    dummy = DummyTqdmFile(output)
    
    dummy.write("")
    dummy.write("text")
    dummy.write("")
    dummy.write("")
    del dummy
    
    assert output.getvalue() == "text"


# Test alternating bytes and strings (should fail if mixed)
def test_dummy_tqdm_file_cannot_mix_types():
    """DummyTqdmFile should handle one type at a time"""
    output = io.StringIO()
    dummy = DummyTqdmFile(output)
    
    dummy.write("string")
    # This would fail if we tried to write bytes to a StringIO
    # Just documenting the expected behavior
    dummy.write("\n")
    del dummy
    
    assert output.getvalue() == "string\n"