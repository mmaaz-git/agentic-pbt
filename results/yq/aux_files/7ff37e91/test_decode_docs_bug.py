#!/usr/bin/env python3
"""Test for potential bug in decode_docs function."""

import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

from yq import decode_docs

def test_decode_docs_no_trailing_character():
    """Test decode_docs with JSON that has no trailing character."""
    decoder = json.JSONDecoder()
    
    # Test case 1: Simple JSON object with no trailing newline
    print("Test 1: JSON with no trailing newline")
    jq_output = '{"key": "value"}'
    print(f"Input: {repr(jq_output)}")
    print(f"Input length: {len(jq_output)}")
    
    try:
        result = list(decode_docs(jq_output, decoder))
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    print()
    
    # Test case 2: Multiple documents, last one has no trailing character
    print("Test 2: Multiple docs, last without trailing")
    jq_output = '{"a": 1}\n{"b": 2}'
    print(f"Input: {repr(jq_output)}")
    
    try:
        result = list(decode_docs(jq_output, decoder))
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    print()
    
    # Test case 3: Single number (minimal JSON)
    print("Test 3: Single number")
    jq_output = '42'
    print(f"Input: {repr(jq_output)}")
    
    try:
        result = list(decode_docs(jq_output, decoder))
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    print()
    
    # Let's understand what raw_decode returns
    print("Understanding raw_decode behavior:")
    test_json = '{"test": true}'
    doc, pos = decoder.raw_decode(test_json)
    print(f"For input: {repr(test_json)}")
    print(f"raw_decode returns: doc={doc}, pos={pos}")
    print(f"String length: {len(test_json)}")
    print(f"pos + 1 = {pos + 1}")
    print(f"Slicing from pos+1: {repr(test_json[pos + 1:])}")

if __name__ == "__main__":
    test_decode_docs_no_trailing_character()