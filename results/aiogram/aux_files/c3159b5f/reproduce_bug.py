"""
Minimal reproduction of the deep_link encoding bug
"""

import aiogram.utils.deep_linking as dl

# A simple 20-character string that when encoded with base64 exceeds 64 chars
text = "0" * 5 + "\x80" * 8 + "𐀀" * 7  

print(f"Input text length: {len(text)} characters")

try:
    # This should work since encode=True is set, but it fails
    link = dl.create_deep_link(
        username="testbot",
        link_type="start",
        payload=text,
        encode=True
    )
    print(f"Success: {link}")
except ValueError as e:
    print(f"Bug! Got error: {e}")
    print("Expected: Should successfully encode any reasonable-length string when encode=True")