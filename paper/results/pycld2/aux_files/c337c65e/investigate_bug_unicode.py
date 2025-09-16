#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pycld2_env/lib/python3.13/site-packages')

import pycld2

print("Testing with various Unicode text:")

test_cases = [
    # (text, description)
    ("", "Empty string"),
    (" ", "Single space"),
    ("A", "Single ASCII char"),
    ("€", "Euro sign (3 bytes in UTF-8)"),
    ("你", "Chinese char (3 bytes)"),
    ("🎉", "Emoji (4 bytes)"),
    ("Hello", "Simple English"),
    ("你好", "Chinese greeting"),
    ("こんにちは", "Japanese greeting"),
    ("مرحبا", "Arabic greeting"),
    ("Привет", "Russian greeting"),
    ("A€B", "Mixed ASCII and multibyte"),
    ("Test🎉", "Text with emoji"),
]

print(f"{'Text':<20} | {'Description':<25} | {'UTF-8 bytes':>11} | {'textBytesFound':>14} | {'Difference':>10}")
print("-" * 95)

for text, description in test_cases:
    result = pycld2.detect(text)
    text_bytes_found = result[1]
    actual_bytes = len(text.encode('utf-8'))
    diff = text_bytes_found - actual_bytes
    
    display_text = repr(text) if len(text) <= 10 else repr(text[:7] + "...")
    print(f"{display_text:<20} | {description:<25} | {actual_bytes:>11} | {text_bytes_found:>14} | {diff:>10}")
    
    if diff != 0:
        print(f"  {'⚠️ BUG:' if diff > 0 else '⚠️ Unexpected:'} Difference of {diff} bytes")

print("\n" + "="*95)
print("Testing with returnVectors=True to see if vectors match:")

for text in ["Hello", "A", "Test🎉", "你好世界"]:
    result = pycld2.detect(text, returnVectors=True)
    isReliable, textBytesFound, details, vectors = result
    actual_bytes = len(text.encode('utf-8'))
    
    print(f"\nText: {repr(text)}")
    print(f"  Actual UTF-8 bytes: {actual_bytes}")
    print(f"  textBytesFound: {textBytesFound} (diff: {textBytesFound - actual_bytes})")
    print(f"  Vectors: {vectors}")
    
    if vectors:
        for offset, length, lang_name, lang_code in vectors:
            print(f"    Vector spans bytes {offset} to {offset + length} ({length} bytes) - {lang_name}")
            if offset + length > actual_bytes:
                print(f"      ⚠️ BUG: Vector extends beyond actual text bytes!")

print("\n" + "="*95)
print("Testing if the bug is related to null terminator or padding:")

# Test if pycld2 might be adding null terminator or BOM
for text in ["A", "AB", "ABC"]:
    result = pycld2.detect(text)
    text_bytes_found = result[1]
    actual_bytes = len(text.encode('utf-8'))
    
    # Check various possibilities
    with_null = len(text.encode('utf-8')) + 1  # null terminator
    with_bom = len(b'\xef\xbb\xbf' + text.encode('utf-8'))  # UTF-8 BOM
    with_double_null = len(text.encode('utf-8')) + 2  # double null
    
    print(f"\nText: {repr(text)}")
    print(f"  Actual bytes: {actual_bytes}")
    print(f"  textBytesFound: {text_bytes_found}")
    print(f"  With null terminator: {with_null}")
    print(f"  With BOM: {with_bom}")
    print(f"  With double null: {with_double_null}")
    
    if text_bytes_found == with_double_null:
        print(f"  → Matches double null terminator pattern!")
    elif text_bytes_found == with_null:
        print(f"  → Matches single null terminator pattern!")
    elif text_bytes_found == actual_bytes + 2:
        print(f"  → Consistently 2 bytes more than actual")