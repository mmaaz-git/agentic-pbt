import math
from hypothesis import given, strategies as st, assume, settings
import pytest
from tqdm.utils import (
    FormatReplace, disp_len, disp_trim, Comparable
)


# Test 1: FormatReplace ignores format specs (docstring claim)
@given(
    replace_text=st.text(),
    format_spec=st.text()
)
def test_format_replace_ignores_spec(replace_text, format_spec):
    """FormatReplace docstring claims format specs are ignored."""
    fr = FormatReplace(replace_text)
    
    # The docstring example shows f"{a:5d}" returns the replacement string
    # So any format spec should return the original replacement text
    formatted = format(fr, format_spec)
    assert formatted == replace_text
    
    # Also test with f-string style
    result = f"{fr:{format_spec}}"
    assert result == replace_text


# Test 2: disp_trim respects display length
@given(
    text=st.text(),
    length=st.integers(min_value=0, max_value=1000)
)
def test_disp_trim_respects_length(text, length):
    """disp_trim should produce strings with display length <= requested."""
    trimmed = disp_trim(text, length)
    actual_display_len = disp_len(trimmed)
    
    # The trimmed string's display length should not exceed requested length
    assert actual_display_len <= length


# Test 3: disp_trim with ANSI codes maintains proper closure
@given(
    text=st.text(min_size=1),
    ansi_code=st.sampled_from(['\x1b[31m', '\x1b[32m', '\x1b[1m', '\x1b[4m']),
    length=st.integers(min_value=0, max_value=100)
)
def test_disp_trim_ansi_closure(text, ansi_code, length):
    """disp_trim should properly close ANSI codes when present."""
    # Create text with ANSI codes
    ansi_text = f"{ansi_code}{text}\x1b[0m"
    
    trimmed = disp_trim(ansi_text, length)
    
    # If ANSI codes are present in result, it should end with reset
    if '\x1b[' in trimmed and trimmed != '':
        assert trimmed.endswith('\x1b[0m'), f"Trimmed ANSI text should end with reset: {trimmed!r}"


# Test 4: Comparable class transitivity
class TestComparable(Comparable):
    def __init__(self, value):
        self._comparable = value


@given(
    a=st.integers(),
    b=st.integers(),
    c=st.integers()
)
def test_comparable_transitivity(a, b, c):
    """Test transitivity: if a < b and b < c, then a < c."""
    obj_a = TestComparable(a)
    obj_b = TestComparable(b)
    obj_c = TestComparable(c)
    
    if obj_a < obj_b and obj_b < obj_c:
        assert obj_a < obj_c
    
    if obj_a <= obj_b and obj_b <= obj_c:
        assert obj_a <= obj_c
    
    if obj_a == obj_b and obj_b == obj_c:
        assert obj_a == obj_c


@given(
    a=st.integers(),
    b=st.integers()
)
def test_comparable_consistency(a, b):
    """Test consistency of comparison operators."""
    obj_a = TestComparable(a)
    obj_b = TestComparable(b)
    
    # Exactly one of these should be true (unless equal)
    lt = obj_a < obj_b
    gt = obj_a > obj_b
    eq = obj_a == obj_b
    
    # Trichotomy: exactly one of <, >, == is true
    assert sum([lt, gt, eq]) == 1
    
    # <= is equivalent to < or ==
    assert (obj_a <= obj_b) == (lt or eq)
    
    # >= is equivalent to > or ==
    assert (obj_a >= obj_b) == (gt or eq)
    
    # != is opposite of ==
    assert (obj_a != obj_b) == (not eq)


# Test 5: disp_len with wide characters
@given(
    ascii_text=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
    wide_char=st.sampled_from(['你', '好', '世', '界', '日', '本', '한', '국'])
)
def test_disp_len_wide_chars(ascii_text, wide_char):
    """Wide characters should count as 2 display units."""
    # ASCII text should have display length equal to string length
    assert disp_len(ascii_text) == len(ascii_text)
    
    # Wide character should have display length of 2
    assert disp_len(wide_char) == 2
    
    # Combined string
    combined = ascii_text + wide_char
    assert disp_len(combined) == len(ascii_text) + 2


# Test 6: disp_trim idempotence for already-short strings
@given(
    text=st.text(max_size=50),
    length=st.integers(min_value=100, max_value=200)
)
def test_disp_trim_idempotent_short(text, length):
    """Trimming to a length longer than the string should return the original."""
    if disp_len(text) <= length:
        trimmed = disp_trim(text, length)
        # For strings already shorter than requested, should be unchanged
        # (unless ANSI codes need closing)
        if '\x1b[' not in text:
            assert trimmed == text