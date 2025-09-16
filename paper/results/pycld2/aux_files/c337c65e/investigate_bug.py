#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pycld2_env/lib/python3.13/site-packages')

import pycld2

# Investigate the bug found: textBytesFound > actual byte length
print("Investigating textBytesFound bug:")

test_cases = [
    "A",
    "AA", 
    "AAA",
    "AAAA",
    "B",
    "AB",
    "ABC",
    "Hello",
    "X",
    "Y",
    "Z",
    "a",
    "ab",
    "abc",
]

for text in test_cases:
    result = pycld2.detect(text)
    text_bytes_found = result[1]
    actual_bytes = len(text.encode('utf-8'))
    
    print(f"Text: '{text:10}' | Actual bytes: {actual_bytes:3} | textBytesFound: {text_bytes_found:3} | Diff: {text_bytes_found - actual_bytes:3}")
    if text_bytes_found > actual_bytes:
        print(f"  ^ BUG: textBytesFound ({text_bytes_found}) > actual bytes ({actual_bytes})")
        print(f"    Full result: {result}")

print("\nTesting with longer text:")
for length in [1, 2, 3, 4, 5, 10, 20, 50, 100]:
    text = "A" * length
    result = pycld2.detect(text)
    text_bytes_found = result[1]
    actual_bytes = len(text.encode('utf-8'))
    if text_bytes_found != actual_bytes:
        print(f"Length {length:3}: Actual {actual_bytes:3}, Found {text_bytes_found:3}, Diff: {text_bytes_found - actual_bytes:3}")

print("\nTesting minimum text needed for detection:")
for i in range(1, 20):
    text = "Hello world! " * i
    result = pycld2.detect(text)
    if result[0]:  # isReliable
        print(f"Reliable detection at {i} repetitions ({len(text)} chars, {len(text.encode('utf-8'))} bytes)")
        print(f"  Result: {result}")
        break