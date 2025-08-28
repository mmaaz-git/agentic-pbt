#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pycld2_env/lib/python3.13/site-packages')

import pycld2
from hypothesis import given, strategies as st, assume, settings
import math

# Strategy for generating valid text inputs
text_strategy = st.text(min_size=0, max_size=1000)
bytes_strategy = st.binary(min_size=0, max_size=1000)

# Property 1: Return format invariant - always returns tuple with 3 or 4 elements
@given(text_strategy, st.booleans())
def test_return_format_invariant(text, return_vectors):
    result = pycld2.detect(text, returnVectors=return_vectors)
    
    assert isinstance(result, tuple)
    if return_vectors:
        assert len(result) == 4
        assert isinstance(result[3], tuple)  # vectors should be a tuple
    else:
        assert len(result) == 3
    
    # Check the structure of the first 3 elements
    assert isinstance(result[0], bool)  # isReliable
    assert isinstance(result[1], int)  # textBytesFound
    assert isinstance(result[2], tuple)  # details
    assert len(result[2]) == 3  # Always 3 language entries
    
    # Each detail entry should be a 4-tuple
    for detail in result[2]:
        assert isinstance(detail, tuple)
        assert len(detail) == 4
        # (languageName, languageCode, percent, score)
        assert isinstance(detail[0], str)  # language name
        assert isinstance(detail[1], str)  # language code
        assert isinstance(detail[2], int)  # percent
        assert isinstance(detail[3], float)  # score


# Property 2: textBytesFound should be <= length of input
@given(text_strategy)
def test_text_bytes_found_invariant(text):
    result = pycld2.detect(text)
    text_bytes_found = result[1]
    
    # Convert text to UTF-8 to get actual byte length
    text_bytes_len = len(text.encode('utf-8'))
    
    assert text_bytes_found <= text_bytes_len


# Property 3: Percentage sum should be <= 100
@given(text_strategy)
def test_percentage_sum_invariant(text):
    result = pycld2.detect(text)
    details = result[2]
    
    # Sum up all percentages
    percentage_sum = sum(detail[2] for detail in details)
    
    assert percentage_sum <= 100


# Property 4: HTML parsing should detect less or equal text than plain text
@given(st.text(alphabet=st.characters(blacklist_characters='\x00'), min_size=0, max_size=500))
def test_html_vs_plain_text_invariant(text):
    # Add some HTML tags to the text
    html_text = f"<html><body>{text}</body></html>"
    
    result_plain = pycld2.detect(html_text, isPlainText=True)
    result_html = pycld2.detect(html_text, isPlainText=False)
    
    bytes_plain = result_plain[1]
    bytes_html = result_html[1]
    
    # HTML mode should detect less or equal bytes (since it strips tags)
    assert bytes_html <= bytes_plain


# Property 5: Idempotence - same input should give same result
@given(text_strategy)
def test_idempotence(text):
    result1 = pycld2.detect(text)
    result2 = pycld2.detect(text)
    
    assert result1 == result2


# Property 6: Both str and UTF-8 bytes should give same result
@given(st.text(min_size=0, max_size=500))
def test_str_bytes_equivalence(text):
    result_str = pycld2.detect(text)
    result_bytes = pycld2.detect(text.encode('utf-8'))
    
    assert result_str == result_bytes


# Property 7: bestEffort should only affect reliability, not crash
@given(text_strategy, st.booleans())
def test_best_effort_no_crash(text, best_effort):
    # Should not crash regardless of bestEffort value
    result = pycld2.detect(text, bestEffort=best_effort)
    assert isinstance(result, tuple)


# Property 8: Vectors byte ranges should be within text bounds
@given(text_strategy)
@settings(max_examples=500)
def test_vectors_bounds(text):
    result = pycld2.detect(text, returnVectors=True)
    vectors = result[3]
    text_bytes_len = len(text.encode('utf-8'))
    
    for offset, length, lang_name, lang_code in vectors:
        assert offset >= 0
        assert length >= 0
        assert offset + length <= text_bytes_len


# Property 9: Non-UTF8 bytes should raise error
@given(bytes_strategy)
def test_invalid_utf8_raises_error(data):
    # Try to decode to ensure it's invalid UTF-8
    try:
        data.decode('utf-8')
        # If it's valid UTF-8, skip this test case
        assume(False)
    except UnicodeDecodeError:
        # This is invalid UTF-8, should raise cld2.error
        try:
            result = pycld2.detect(data)
            # If we get here without error, that's a bug
            assert False, f"Expected cld2.error for invalid UTF-8, got {result}"
        except pycld2.error:
            # Expected behavior
            pass


# Property 10: Score values should be non-negative
@given(text_strategy)
def test_score_non_negative(text):
    result = pycld2.detect(text)
    details = result[2]
    
    for detail in details:
        score = detail[3]
        assert score >= 0.0


# Property 11: Language codes should be valid (2-3 chars or 'un' for unknown)
@given(text_strategy)
def test_language_code_format(text):
    result = pycld2.detect(text)
    details = result[2]
    
    for detail in details:
        lang_code = detail[1]
        # Should be 2-3 character codes or 'un' for unknown
        assert len(lang_code) in [2, 3] or lang_code == 'un'
        # Should be lowercase
        assert lang_code == lang_code.lower()


if __name__ == "__main__":
    print("Running property-based tests for pycld2...")
    
    # Run each test with a small number of examples for quick feedback
    test_functions = [
        test_return_format_invariant,
        test_text_bytes_found_invariant,
        test_percentage_sum_invariant,
        test_html_vs_plain_text_invariant,
        test_idempotence,
        test_str_bytes_equivalence,
        test_best_effort_no_crash,
        test_vectors_bounds,
        test_invalid_utf8_raises_error,
        test_score_non_negative,
        test_language_code_format,
    ]
    
    for test_func in test_functions:
        print(f"  Testing: {test_func.__name__}...", end=" ")
        try:
            test_func()
            print("✓")
        except Exception as e:
            print(f"✗ - {e}")
    
    print("\nTests complete! Run with pytest for full testing.")