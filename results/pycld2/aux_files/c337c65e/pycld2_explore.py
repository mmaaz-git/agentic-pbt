#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pycld2_env/lib/python3.13/site-packages')

import pycld2

# Test various edge cases and functionality
print("Testing detect function with various inputs:")

# Test 1: Basic functionality
text1 = "The quick brown fox jumps over the lazy dog."
result1 = pycld2.detect(text1)
print(f"\n1. English text: {text1}")
print(f"   Result: {result1}")

# Test 2: returnVectors parameter
result2 = pycld2.detect(text1, returnVectors=True)
print(f"\n2. With returnVectors=True:")
print(f"   Result has {len(result2)} elements")
if len(result2) > 3:
    print(f"   Vectors: {result2[3]}")

# Test 3: Mixed language text
mixed_text = "Hello world! Bonjour le monde! Hola mundo!"
result3 = pycld2.detect(mixed_text)
print(f"\n3. Mixed language: {mixed_text}")
print(f"   Result: {result3}")

# Test 4: Non-plain text (HTML)
html_text = "<html><body>Hello world!</body></html>"
result4_plain = pycld2.detect(html_text, isPlainText=True)
result4_html = pycld2.detect(html_text, isPlainText=False)
print(f"\n4. HTML text: {html_text}")
print(f"   As plain text: {result4_plain}")
print(f"   As HTML: {result4_html}")

# Test 5: Hint parameters
result5 = pycld2.detect("ciao", hintLanguage="it")
result5_no_hint = pycld2.detect("ciao")
print(f"\n5. With Italian hint for 'ciao':")
print(f"   With hint: {result5}")
print(f"   Without hint: {result5_no_hint}")

# Test 6: bestEffort for short text
short_text = "Hi"
result6_normal = pycld2.detect(short_text)
result6_best = pycld2.detect(short_text, bestEffort=True)
print(f"\n6. Short text '{short_text}':")
print(f"   Normal: {result6_normal}")
print(f"   Best effort: {result6_best}")

# Test 7: Check if bytes input works
bytes_text = "Hello world!".encode('utf-8')
result7 = pycld2.detect(bytes_text)
print(f"\n7. Bytes input: {bytes_text}")
print(f"   Result: {result7}")

# Test 8: Unicode text
unicode_text = "こんにちは世界 🌍 Hello"
result8 = pycld2.detect(unicode_text)
print(f"\n8. Unicode with emoji: {unicode_text}")
print(f"   Result: {result8}")

# Test 9: Empty and whitespace
empty_results = []
for test_str in ["", " ", "   ", "\n", "\t\n"]:
    try:
        res = pycld2.detect(test_str)
        empty_results.append((repr(test_str), res))
    except Exception as e:
        empty_results.append((repr(test_str), f"Error: {e}"))

print(f"\n9. Empty/whitespace strings:")
for inp, res in empty_results:
    print(f"   {inp}: {res}")