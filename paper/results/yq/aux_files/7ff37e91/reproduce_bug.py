#!/usr/bin/env python3
"""Minimal reproduction of the decode_docs bug."""

import json

def decode_docs(jq_output, json_decoder):
    """This is the function from yq/__init__.py lines 38-43"""
    while jq_output:
        doc, pos = json_decoder.raw_decode(jq_output)
        jq_output = jq_output[pos + 1 :]  # BUG: pos+1 can be out of bounds
        yield doc

# Demonstration of the bug
decoder = json.JSONDecoder()

# This will fail with an infinite loop or incorrect behavior
print("Testing decode_docs with JSON that has no trailing newline:")
jq_output = '{"key": "value"}'
print(f"Input: {repr(jq_output)}")

try:
    # First, let's see what raw_decode returns
    doc, pos = decoder.raw_decode(jq_output)
    print(f"raw_decode returns: doc={doc}, pos={pos}")
    print(f"String length: {len(jq_output)}")
    print(f"Attempting to slice from pos+1={pos+1}")
    print(f"jq_output[pos+1:] = {repr(jq_output[pos+1:])}")
    print()
    
    # Now run the actual function
    print("Running decode_docs:")
    result = list(decode_docs('{"key": "value"}', decoder))
    print(f"Result: {result}")
    print("Success - but might have issues with edge cases")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

print("\n" + "="*50 + "\n")

# More problematic case
print("Testing with numeric JSON (minimal case):")
jq_output = '0'
print(f"Input: {repr(jq_output)}")

try:
    doc, pos = decoder.raw_decode(jq_output)
    print(f"raw_decode returns: doc={doc}, pos={pos}")
    print(f"String length: {len(jq_output)}")
    print(f"Attempting to slice from pos+1={pos+1}")
    # This will create an empty string
    remaining = jq_output[pos+1:]
    print(f"jq_output[pos+1:] = {repr(remaining)}")
    
    # The while loop will terminate because empty string is falsy
    # So single documents work, but the logic is flawed
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

print("\n" + "="*50 + "\n")

# The real issue: what if there's content immediately after?
print("Testing back-to-back JSON documents:")
jq_output = '{"a":1}{"b":2}'
print(f"Input: {repr(jq_output)}")

try:
    result = list(decode_docs('{"a":1}{"b":2}', decoder))
    print(f"Result: {result}")
    print("This demonstrates the function can miss documents!")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")