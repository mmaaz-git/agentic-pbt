#!/usr/bin/env python3
"""
Minimal reproduction of SQL escaping bug in quickbooks.utils
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.utils import build_where_clause, build_choose_clause


def main():
    print("=== SQL Escaping Bug in quickbooks.utils ===\n")
    
    # Test case 1: Simple name with apostrophe
    print("Test 1: Name with apostrophe")
    name = "O'Brien"
    result = build_where_clause(LastName=name)
    print(f"Input: {name}")
    print(f"Output: {result}")
    print(f"Correct SQL-92: LastName = 'O''Brien'")
    print(f"Bug: Uses backslash escaping instead of quote doubling\n")
    
    # Test case 2: Multiple quotes
    print("Test 2: Multiple quotes")
    text = "'''"
    result = build_where_clause(field=text)
    print(f"Input: {text}")
    print(f"Output: {result}")
    print(f"Correct SQL-92: field = ''''''''")
    print(f"Bug: Uses \\' instead of ''\n")
    
    # Test case 3: SQL injection attempt
    print("Test 3: Potential SQL injection")
    malicious = "'; DROP TABLE users; --"
    result = build_where_clause(comment=malicious)
    print(f"Input: {malicious}")
    print(f"Output: {result}")
    print(f"Note: If the database doesn't handle \\' properly, this could be dangerous\n")
    
    # Test case 4: build_choose_clause
    print("Test 4: build_choose_clause with quotes")
    choices = ["O'Brien", "John's"]
    result = build_choose_clause(choices, "LastName")
    print(f"Choices: {choices}")
    print(f"Output: {result}")
    print(f"Correct SQL-92: LastName in ('O''Brien', 'John''s')")
    print(f"Bug: Uses backslash escaping\n")
    
    print("=== Summary ===")
    print("The functions use .replace(r\"'\", r\"\\'\") for escaping.")
    print("This is incorrect for SQL-92 standard, which requires doubling quotes.")
    print("Most SQL databases expect '' not \\' for escaping single quotes.")
    print("This could cause:")
    print("1. SQL syntax errors in standard-compliant databases")
    print("2. Security vulnerabilities if backslash escaping isn't handled")
    print("3. Compatibility issues across different SQL engines")


if __name__ == "__main__":
    main()