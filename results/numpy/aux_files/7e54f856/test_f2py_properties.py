"""Property-based tests for numpy.f2py module."""

import string
import random
from hypothesis import given, strategies as st, settings, assume
import numpy.f2py.crackfortran as cf


# Test 1: Round-trip property for markouterparen/unmarkouterparen
@given(st.text(alphabet=string.ascii_letters + string.digits + "(),. \t"))
def test_markouterparen_round_trip(text):
    """markouterparen and unmarkouterparen should be inverse operations."""
    marked = cf.markouterparen(text)
    unmarked = cf.unmarkouterparen(marked)
    assert text == unmarked, f"Round-trip failed: {text!r} -> {marked!r} -> {unmarked!r}"


# Test 2: markouterparen should preserve non-parentheses characters
@given(st.text(alphabet=string.ascii_letters + string.digits + " ,.\t", min_size=1))
def test_markouterparen_preserves_non_parens(text):
    """markouterparen should not modify strings without parentheses."""
    assume("(" not in text and ")" not in text)
    marked = cf.markouterparen(text)
    # The string should be unchanged since there are no parentheses
    assert text == marked, f"Modified non-paren string: {text!r} -> {marked!r}"


# Test 3: stripcomma idempotence property
@given(st.text())
def test_stripcomma_idempotent(text):
    """Applying stripcomma twice should give the same result as applying it once."""
    once = cf.stripcomma(text)
    twice = cf.stripcomma(once)
    assert once == twice, f"Not idempotent: stripcomma({text!r}) = {once!r}, stripcomma(stripcomma({text!r})) = {twice!r}"


# Test 4: stripcomma should only remove trailing commas
@given(st.text(min_size=1))
def test_stripcomma_only_trailing(text):
    """stripcomma should preserve all characters except trailing commas."""
    result = cf.stripcomma(text)
    # Result should be a prefix of the original
    assert text.startswith(result), f"Result not a prefix: {text!r} -> {result!r}"
    # The removed part should only be commas
    removed = text[len(result):]
    assert all(c == ',' for c in removed), f"Removed non-comma chars: {removed!r}"


# Test 5: markoutercomma marking property
@given(st.text(alphabet=string.ascii_letters + string.digits + "(),. \t"))
def test_markoutercomma_marks_commas(text):
    """markoutercomma should mark commas that are not inside parentheses."""
    marked = cf.markoutercomma(text)
    # Count the number of '@,@' markers - should equal outer commas
    paren_depth = 0
    outer_comma_count = 0
    for char in text:
        if char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth = max(0, paren_depth - 1)
        elif char == ',' and paren_depth == 0:
            outer_comma_count += 1
    
    marker_count = marked.count('@,@')
    assert marker_count == outer_comma_count, f"Marker count mismatch: expected {outer_comma_count}, got {marker_count} for {text!r}"


# Test 6: removespaces should be idempotent
@given(st.text())
def test_removespaces_idempotent(text):
    """Applying removespaces twice should give the same result as applying it once."""
    once = cf.removespaces(text)
    twice = cf.removespaces(once)
    assert once == twice, f"Not idempotent: removespaces({text!r}) = {once!r}, removespaces(removespaces({text!r})) = {twice!r}"


# Test 7: markinnerspaces preserves string length or increases it
@given(st.text())
def test_markinnerspaces_length(text):
    """markinnerspaces should preserve or increase the string length."""
    marked = cf.markinnerspaces(text)
    assert len(marked) >= len(text), f"String got shorter: {len(text)} -> {len(marked)}"


# Test 8: split_by_unquoted should handle empty separators gracefully
@given(st.text(min_size=1))
def test_split_by_unquoted_with_char(text):
    """split_by_unquoted should return a tuple (part, has_separator)."""
    # Test with semicolon
    result = cf.split_by_unquoted(text, ";")
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2-tuple, got {len(result)}-tuple"
    part, has_separator = result
    assert isinstance(has_separator, (bool, str)), f"Expected bool or str for has_separator, got {type(has_separator)}"


# Test 9: Multiple marking/unmarking should preserve the original
@given(st.text(alphabet=string.ascii_letters + string.digits + "(),. \t"))
@settings(max_examples=100)
def test_multiple_mark_unmark_cycles(text):
    """Multiple cycles of marking and unmarking should preserve the original."""
    current = text
    for _ in range(3):
        current = cf.markouterparen(current)
        current = cf.unmarkouterparen(current)
    assert current == text, f"Multiple cycles changed text: {text!r} -> {current!r}"


# Test 10: Check if @ is properly escaped in markouterparen
@given(st.text(alphabet=string.ascii_letters + string.digits + "(),. \t@"))
def test_markouterparen_with_at_symbol(text):
    """markouterparen should handle @ symbols in the input correctly."""
    # If the input contains @, marking should still work
    marked = cf.markouterparen(text)
    unmarked = cf.unmarkouterparen(marked)
    assert text == unmarked, f"Round-trip with @ failed: {text!r} -> {marked!r} -> {unmarked!r}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])