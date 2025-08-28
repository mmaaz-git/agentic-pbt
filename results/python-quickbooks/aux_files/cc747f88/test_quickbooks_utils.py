#!/usr/bin/env python3
"""
Property-based tests for quickbooks.utils module.
Testing critical properties claimed by the implementation.
"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
from quickbooks.utils import build_where_clause, build_choose_clause


# Strategy for SQL-like field names
field_names = st.text(alphabet=st.characters(whitelist_categories=('L', 'Nd'), whitelist_characters='_'), min_size=1)


@given(st.dictionaries(
    field_names,
    st.one_of(
        st.text(),  # String values
        st.integers(),  # Integer values
        st.floats(allow_nan=False, allow_infinity=False),  # Float values
    )
))
def test_build_where_clause_quote_escaping(kwargs):
    """Test that single quotes in string values are properly escaped."""
    result = build_where_clause(**kwargs)
    
    # Check each string value's quote escaping
    for key, value in kwargs.items():
        if isinstance(value, str):
            # Count unescaped single quotes in the original value
            unescaped_quotes = value.count("'") - value.count(r"\'")
            
            # The function should escape all single quotes
            # Expected pattern: key = 'escaped_value'
            if unescaped_quotes > 0:
                # Verify quotes are escaped in the output
                expected_escaped = value.replace(r"'", r"\'")
                assert expected_escaped in result or (key + " = '" + expected_escaped + "'") in result


@given(st.dictionaries(field_names, st.text(alphabet=st.characters()), min_size=0, max_size=10))
def test_build_where_clause_empty_input(kwargs):
    """Test that empty input produces empty string."""
    if len(kwargs) == 0:
        assert build_where_clause(**kwargs) == ""
    else:
        assert build_where_clause(**kwargs) != ""


@given(st.dictionaries(
    field_names,
    st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
    min_size=2
))
def test_build_where_clause_and_joining(kwargs):
    """Test that multiple conditions are joined with AND."""
    result = build_where_clause(**kwargs)
    
    if len(kwargs) > 1:
        # Should have (n-1) AND operators for n conditions
        assert result.count(" AND ") == len(kwargs) - 1


@given(st.dictionaries(
    field_names,
    st.one_of(st.text(), st.integers()),
    min_size=1
))
def test_build_where_clause_string_vs_nonstring_format(kwargs):
    """Test that strings are quoted but non-strings are not."""
    result = build_where_clause(**kwargs)
    
    for key, value in kwargs.items():
        if isinstance(value, str):
            # Strings should be wrapped in single quotes
            assert f"{key} = '" in result
        else:
            # Non-strings should not have quotes around the value
            assert f"{key} = {value}" in result


@given(
    st.lists(st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False))),
    field_names
)
def test_build_choose_clause_quote_escaping(choices, field):
    """Test that single quotes in string choices are properly escaped."""
    result = build_choose_clause(choices, field)
    
    for choice in choices:
        if isinstance(choice, str) and "'" in choice:
            # The function claims to escape quotes
            escaped_choice = choice.replace(r"'", r"\'")
            if len(choices) > 0:
                assert escaped_choice in result or f"'{escaped_choice}'" in result


@given(st.lists(st.one_of(st.text(), st.integers()), min_size=0), field_names)
def test_build_choose_clause_empty_input(choices, field):
    """Test that empty choices list produces empty string."""
    result = build_choose_clause(choices, field)
    
    if len(choices) == 0:
        assert result == ""
    else:
        assert result.startswith(f"{field} in (")
        assert result.endswith(")")


@given(
    st.lists(st.one_of(st.text(min_size=1), st.integers()), min_size=1, max_size=10),
    field_names
)
def test_build_choose_clause_format(choices, field):
    """Test the IN clause format and comma separation."""
    result = build_choose_clause(choices, field)
    
    # Should have the format: field in (value1, value2, ...)
    assert result.startswith(f"{field} in (")
    assert result.endswith(")")
    
    # Should have (n-1) commas for n choices
    if len(choices) > 1:
        inner_part = result[len(f"{field} in ("):-1]
        assert inner_part.count(", ") >= len(choices) - 1


@given(st.text())
def test_build_where_clause_single_quote_edge_cases(text):
    """Test various edge cases with single quotes."""
    # Test with text containing single quotes
    kwargs = {"field": text}
    result = build_where_clause(**kwargs)
    
    # The result should be parseable and not break SQL syntax
    if text:
        assert "field = " in result
        # Check that the value part is properly quoted
        if "'" in text:
            # Original implementation uses .replace(r"'", r"\'")
            # This is actually incorrect escaping for SQL! 
            # In SQL, single quotes should be escaped as '' not \'
            pass  # We'll check if this causes issues


@given(st.text(alphabet="'", min_size=1))
def test_quote_only_strings(text):
    """Test strings that contain only single quotes."""
    
    kwargs = {"field": text}
    result = build_where_clause(**kwargs)
    
    # Should still produce valid output
    assert "field = " in result
    
    choices = [text]
    result2 = build_choose_clause(choices, "field")
    if result2:  # Not empty
        assert "field in (" in result2