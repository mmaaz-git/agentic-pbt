"""
Property-based tests for Cython.Plex using Hypothesis
"""

import string
from hypothesis import given, strategies as st, assume, settings
import Cython.Plex as Plex
from Cython.Plex.Regexps import (
    chars_to_ranges, uppercase_range, lowercase_range,
    Seq, Alt, Rep, Rep1, Opt, Empty, Str, Any, AnyBut, AnyChar
)


# Test 1: chars_to_ranges produces sorted, non-overlapping ranges
@given(st.text(min_size=0, max_size=100))
def test_chars_to_ranges_produces_sorted_ranges(s):
    """Test that chars_to_ranges produces sorted, non-overlapping ranges"""
    ranges = chars_to_ranges(s)
    
    # Should have even length (pairs of start, end)
    assert len(ranges) % 2 == 0
    
    # Each pair should be [start, end) with start < end
    for i in range(0, len(ranges), 2):
        start, end = ranges[i], ranges[i+1]
        assert start < end, f"Range [{start}, {end}) is invalid"
    
    # Ranges should be sorted and non-overlapping
    for i in range(2, len(ranges), 2):
        prev_end = ranges[i-1]
        curr_start = ranges[i]
        assert prev_end <= curr_start, f"Ranges overlap or not sorted: prev_end={prev_end}, curr_start={curr_start}"


# Test 2: chars_to_ranges covers all input characters
@given(st.text(min_size=1, max_size=50))
def test_chars_to_ranges_covers_all_chars(s):
    """Test that chars_to_ranges covers all characters in input"""
    ranges = chars_to_ranges(s)
    
    # Convert ranges back to character set
    covered_chars = set()
    for i in range(0, len(ranges), 2):
        start, end = ranges[i], ranges[i+1]
        for code in range(start, end):
            covered_chars.add(chr(code))
    
    # All input characters should be covered
    input_chars = set(s)
    assert input_chars <= covered_chars, f"Missing chars: {input_chars - covered_chars}"


# Test 3: uppercase_range and lowercase_range properties
@given(st.integers(min_value=0, max_value=127),
       st.integers(min_value=0, max_value=127))
def test_case_conversion_ranges(code1, code2):
    """Test uppercase_range and lowercase_range functions"""
    # Ensure code1 <= code2
    if code1 > code2:
        code1, code2 = code2, code1
    
    upper = uppercase_range(code1, code2)
    lower = lowercase_range(code1, code2)
    
    # Check if ranges make sense
    if upper is not None:
        u_start, u_end = upper
        # Should be uppercase letters
        assert ord('A') <= u_start < u_end <= ord('Z') + 1
        # Original range should contain lowercase letters
        assert max(code1, ord('a')) < min(code2, ord('z') + 1)
    
    if lower is not None:
        l_start, l_end = lower
        # Should be lowercase letters 
        assert ord('a') <= l_start < l_end <= ord('z') + 1
        # Original range should contain uppercase letters
        assert max(code1, ord('A')) < min(code2, ord('Z') + 1)


# Test 4: Rep(re) = Opt(Rep1(re)) identity
@given(st.text(min_size=1, max_size=10))
def test_rep_equals_opt_rep1(s):
    """Test that Rep(re) behaves identically to Opt(Rep1(re))"""
    # Create a simple RE from the string
    re = Str(s)
    
    # According to line 494: Rep(re) = Opt(Rep1(re))
    rep_re = Rep(re)
    opt_rep1_re = Opt(Rep1(re))
    
    # Check nullable property
    assert rep_re.nullable == opt_rep1_re.nullable
    
    # Check match_nl property
    assert rep_re.match_nl == opt_rep1_re.match_nl
    
    # String representations should indicate the equivalence
    assert "Rep(" in str(rep_re)
    assert "Opt(Rep1(" in str(opt_rep1_re)


# Test 5: Opt(re) = Alt(re, Empty) identity
@given(st.text(min_size=1, max_size=10))
def test_opt_equals_alt_empty(s):
    """Test that Opt(re) behaves identically to Alt(re, Empty)"""
    re = Str(s)
    
    # According to line 485: Opt(re) = Alt(re, Empty)
    opt_re = Opt(re)
    alt_re = Alt(re, Empty)
    
    # Both should be nullable (can match empty string)
    assert opt_re.nullable == 1
    assert alt_re.nullable == 1
    
    # Check match_nl property
    assert opt_re.match_nl == alt_re.match_nl


# Test 6: Seq operator overloading
@given(st.text(min_size=1, max_size=5),
       st.text(min_size=1, max_size=5))
def test_seq_operator_overloading(s1, s2):
    """Test that re1 + re2 creates Seq(re1, re2)"""
    re1 = Str(s1)
    re2 = Str(s2)
    
    # Using + operator (line 139-140)
    seq_plus = re1 + re2
    # Direct construction
    seq_direct = Seq(re1, re2)
    
    # Both should be Seq instances
    assert isinstance(seq_plus, Seq)
    assert isinstance(seq_direct, Seq)
    
    # Properties should match
    assert seq_plus.nullable == seq_direct.nullable
    assert seq_plus.match_nl == seq_direct.match_nl


# Test 7: Alt operator overloading
@given(st.text(min_size=1, max_size=5),
       st.text(min_size=1, max_size=5))
def test_alt_operator_overloading(s1, s2):
    """Test that re1 | re2 creates Alt(re1, re2)"""
    re1 = Str(s1)
    re2 = Str(s2)
    
    # Using | operator (line 142-143)
    alt_pipe = re1 | re2
    # Direct construction
    alt_direct = Alt(re1, re2)
    
    # Both should be Alt instances
    assert isinstance(alt_pipe, Alt)
    assert isinstance(alt_direct, Alt)
    
    # Properties should match
    assert alt_pipe.nullable == alt_direct.nullable
    assert alt_pipe.match_nl == alt_direct.match_nl


# Test 8: Empty sequence properties
@given(st.lists(st.text(min_size=1, max_size=5), min_size=0, max_size=5))
def test_seq_empty_handling(strings):
    """Test Seq with various combinations including Empty"""
    res = [Str(s) for s in strings]
    
    if len(res) == 0:
        # Empty Seq should equal Empty
        seq = Seq()
        assert seq.nullable == 1  # Empty matches empty string
        assert seq.nullable == Empty.nullable
    else:
        seq = Seq(*res)
        # Seq is nullable only if all components are nullable
        expected_nullable = all(r.nullable for r in res)
        assert seq.nullable == (1 if expected_nullable else 0)


# Test 9: AnyChar = AnyBut("") identity
def test_anychar_equals_anybut_empty():
    """Test that AnyChar is equivalent to AnyBut("")"""
    # According to line 454: AnyChar = AnyBut("")
    
    # Both should match newlines
    assert AnyChar.match_nl == 1
    assert AnyBut("").match_nl == 1
    
    # String representations
    assert str(AnyChar) == "AnyChar"
    assert "AnyBut" in str(AnyBut(""))


# Test 10: Any and AnyBut complementarity
@given(st.text(alphabet=string.printable, min_size=1, max_size=20))
def test_any_anybut_complement(chars):
    """Test that Any(s) and AnyBut(s) are complementary"""
    assume(len(set(chars)) > 0)  # Need at least one unique character
    
    any_re = Any(chars)
    anybut_re = AnyBut(chars)
    
    # Any should not be nullable (needs to match a character)
    assert any_re.nullable == 0
    
    # AnyBut should not be nullable either
    assert anybut_re.nullable == 0
    
    # AnyBut can match newline, Any cannot (unless newline is in chars)
    if '\n' not in chars:
        assert any_re.match_nl == 0
        assert anybut_re.match_nl == 1
    else:
        assert any_re.match_nl == 1


# Test 11: Str with multiple strings creates Alt
@given(st.lists(st.text(min_size=1, max_size=5), min_size=2, max_size=5))
def test_str_multiple_creates_alt(strings):
    """Test that Str(s1, s2, ...) creates Alt of individual Strs"""
    result = Str(*strings)
    
    # Should create an Alt
    assert isinstance(result, Alt)
    
    # String representation should show it's a Str with multiple args
    assert "Str(" in str(result)
    
    # Should have the right number of alternatives
    assert len(result.re_list) == len(strings)