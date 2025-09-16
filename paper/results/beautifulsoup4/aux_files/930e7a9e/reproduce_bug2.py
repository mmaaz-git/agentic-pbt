"""Minimal reproduction for bug 2: UnicodeDammit reports utf-8 for non-UTF-8 data."""

import bs4.dammit

# Test case that failed
data = b'\x00\x00\x9d'

# Create UnicodeDammit instance
ud = bs4.dammit.UnicodeDammit(data)

print(f"Input bytes: {data}")
print(f"Detected encoding: {ud.original_encoding}")
print(f"Unicode markup: {ud.unicode_markup!r}")
print(f"Contains replacement chars: {ud.contains_replacement_characters}")
print(f"Tried encodings: {ud.tried_encodings}")

# Try to decode with the reported encoding
print(f"\nTrying to decode with reported encoding '{ud.original_encoding}':")
try:
    decoded = data.decode(ud.original_encoding, errors='strict')
    print(f"✓ Successfully decoded: {decoded!r}")
except UnicodeDecodeError as e:
    print(f"❌ BUG CONFIRMED: Cannot decode with {ud.original_encoding}: {e}")
    
# Check what the actual result is
print(f"\nActual UnicodeDammit result: {ud.unicode_markup!r}")
if '\ufffd' in ud.unicode_markup:
    print("Contains replacement character (U+FFFD)")