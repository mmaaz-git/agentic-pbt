#!/usr/bin/env python3
"""
Property test that demonstrates incorrect SQL escaping in quickbooks.utils.
The functions use backslash escaping instead of SQL standard quote doubling.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from quickbooks.utils import build_where_clause, build_choose_clause


@given(st.text(min_size=1).filter(lambda x: "'" in x))
@settings(max_examples=100)
def test_sql_standard_quote_escaping(text):
    """
    Test that the escaping follows SQL standard (doubling quotes).
    SQL standard: single quotes should be escaped as '' not \'
    """
    result = build_where_clause(field=text)
    
    # Count single quotes in input
    quote_count = text.count("'")
    
    # In SQL standard, each quote should be doubled
    # So we expect to see 2 * quote_count quotes in the escaped value
    # But the function uses backslash escaping instead
    
    # Check that backslash escaping is used (the bug)
    assert r"\'" in result, f"Expected backslash escaping but got: {result}"
    
    # The correct SQL escaping would be:
    correct_escaped = text.replace("'", "''")
    correct_result = f"field = '{correct_escaped}'"
    
    # Demonstrate the difference
    if result != correct_result:
        print(f"\nFound SQL escaping bug!")
        print(f"Input: {text!r}")
        print(f"Actual result: {result}")
        print(f"Correct SQL:   {correct_result}")
        print(f"This violates SQL-92 standard for string literals")
        return False
    
    return True


@given(st.text(alphabet="'", min_size=1, max_size=5))
def test_multiple_quotes_escaping(text):
    """Test that multiple consecutive quotes are handled incorrectly."""
    result = build_where_clause(field=text)
    
    # With SQL standard, ''' would become '''''''' (each quote doubled)
    correct_escaped = text.replace("'", "''")
    correct_result = f"field = '{correct_escaped}'"
    
    # But the function uses backslash escaping
    assert result != correct_result
    print(f"\nMultiple quotes bug:")
    print(f"Input: {text!r}")
    print(f"Got:      {result}")
    print(f"Expected: {correct_result}")


if __name__ == "__main__":
    # Run the property test
    test_sql_standard_quote_escaping("O'Brien")
    test_multiple_quotes_escaping("'''")