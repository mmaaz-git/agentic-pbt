"""Minimal reproduction for bug 1: UnicodeDammit converts b'^' incorrectly."""

import bs4.dammit

# Test case that failed
data = b'^'
expected = '^'

# Create UnicodeDammit instance
ud = bs4.dammit.UnicodeDammit(data)

print(f"Input bytes: {data}")
print(f"Expected output: {expected!r}")
print(f"Actual output: {ud.unicode_markup!r}")
print(f"Detected encoding: {ud.original_encoding}")
print(f"Contains replacement chars: {ud.contains_replacement_characters}")
print(f"Tried encodings: {ud.tried_encodings}")

# Verify the bug
if ud.unicode_markup != expected:
    print(f"\n❌ BUG CONFIRMED: Expected '{expected}' but got '{ud.unicode_markup}'")
else:
    print("\n✓ No bug - output matches expected")