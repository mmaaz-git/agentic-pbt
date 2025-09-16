#!/usr/bin/env python3
"""
Test for SQL injection vulnerability in quickbooks.utils.
The functions claim to escape single quotes but use incorrect escaping for SQL.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.utils import build_where_clause, build_choose_clause


def test_sql_escape_vulnerability():
    """
    In SQL, single quotes should be escaped by doubling them (''),
    not with backslash (\').
    """
    
    # Test 1: Simple single quote
    text_with_quote = "O'Brien"
    result = build_where_clause(name=text_with_quote)
    print(f"Input: {text_with_quote}")
    print(f"Result: {result}")
    print(f"Expected (SQL standard): name = 'O''Brien'")
    print(f"Got backslash escape: {r"\'" in result}")
    print()
    
    # Test 2: Multiple quotes
    text_with_quotes = "It's John's"
    result = build_where_clause(field=text_with_quotes)
    print(f"Input: {text_with_quotes}")
    print(f"Result: {result}")
    print(f"Expected (SQL standard): field = 'It''s John''s'")
    print()
    
    # Test 3: Already escaped with backslash (edge case)
    text_escaped = r"It\'s"
    result = build_where_clause(field=text_escaped)
    print(f"Input (raw): {text_escaped}")
    print(f"Result: {result}")
    print(f"Note: The r prefix means the input has literal backslash-quote")
    print()
    
    # Test 4: build_choose_clause
    choices = ["O'Brien", "Smith's", "regular"]
    result = build_choose_clause(choices, "LastName")
    print(f"Choices: {choices}")
    print(f"Result: {result}")
    print(f"Expected (SQL): LastName in ('O''Brien', 'Smith''s', 'regular')")
    print()
    
    # Test 5: Potential injection if used with certain SQL engines
    # Some SQL engines might not handle \' properly
    malicious = "'; DROP TABLE users; --"
    result = build_where_clause(field=malicious)
    print(f"Potentially malicious input: {malicious}")
    print(f"Result: {result}")
    print(f"If backslash escaping is not handled by the SQL engine, this could be dangerous")
    print()
    
    return result


if __name__ == "__main__":
    test_sql_escape_vulnerability()