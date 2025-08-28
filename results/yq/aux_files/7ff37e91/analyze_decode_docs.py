#!/usr/bin/env python3
"""Analyze the decode_docs function for potential bugs."""

import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

from yq import decode_docs

# Let's test the decode_docs function with edge cases
def test_decode_docs_edge_cases():
    decoder = json.JSONDecoder()
    
    # Test 1: Empty document with just newline
    print("Test 1: Empty with newline")
    result = list(decode_docs("\n", decoder))
    print(f"Result: {result}")
    print()
    
    # Test 2: Multiple newlines
    print("Test 2: Multiple newlines")
    result = list(decode_docs("\n\n\n", decoder))
    print(f"Result: {result}")
    print()
    
    # Test 3: Document without trailing newline
    print("Test 3: No trailing newline")
    doc = '{"key": "value"}'
    result = list(decode_docs(doc, decoder))
    print(f"Result: {result}")
    print()
    
    # Test 4: Multiple documents without spacing
    print("Test 4: Documents back-to-back")
    docs = '{"a": 1}{"b": 2}'
    result = list(decode_docs(docs, decoder))
    print(f"Result: {result}")
    print()
    
    # Test 5: Document with trailing spaces
    print("Test 5: Trailing spaces")
    doc = '{"key": "value"}   '
    result = list(decode_docs(doc, decoder))
    print(f"Result: {result}")
    print()

if __name__ == "__main__":
    test_decode_docs_edge_cases()