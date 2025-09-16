import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.encode import url_quote
from urllib.parse import quote, unquote

# Test with a simple ASCII character - should work
ascii_text = "/"
result = url_quote(ascii_text, safe="/")
print(f"ASCII test: url_quote('/', safe='/') = '{result}'")
print(f"  Expected: '/' (unencoded)")
print(f"  Got: '{result}' - {'✓ PASS' if result == '/' else '✗ FAIL'}")

print("\n" + "="*50 + "\n")

# Test with non-ASCII character - this is the bug
unicode_char = "€"  # Euro sign
result = url_quote(unicode_char, safe="€")
print(f"Non-ASCII test: url_quote('€', safe='€') = '{result}'")
print(f"  Expected: '€' (unencoded)")
print(f"  Got: '{result}' - {'✓ PASS' if '€' in result else '✗ FAIL'}")

# Show what's happening
print(f"\nWhat's happening:")
print(f"  '€' encoded to UTF-8: {repr('€'.encode('utf-8'))}")
print(f"  url_quote passes safe='€' to stdlib quote")
print(f"  But stdlib quote expects safe to contain the UTF-8 bytes, not the character")

print("\n" + "="*50 + "\n")

# Another example with a different character
char = "ñ"
result = url_quote(char, safe="ñ")
print(f"Another test: url_quote('ñ', safe='ñ') = '{result}'")
print(f"  Expected: 'ñ' (unencoded)")
print(f"  Got: '{result}' - {'✓ PASS' if 'ñ' in result else '✗ FAIL'}")

# What the correct implementation should do
print("\nCorrect implementation would need to:")
print("1. Encode the safe characters to UTF-8")
print("2. Pass the encoded bytes as safe parameter")
print("3. This way multi-byte UTF-8 sequences would be preserved")