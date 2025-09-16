#!/usr/bin/env python3
"""Understand why Python's AST normalizes Unicode characters."""

import ast
import unicodedata

# The problematic character
micro_sign = 'µ'  # U+00B5

print("Understanding Python AST Unicode normalization:\n")
print("=" * 70)

# Check Unicode properties
print(f"Character: '{micro_sign}'")
print(f"Unicode code point: U+{ord(micro_sign):04X}")
print(f"Unicode name: {unicodedata.name(micro_sign)}")
print(f"Unicode category: {unicodedata.category(micro_sign)}")

# Check normalization forms
nfc = unicodedata.normalize('NFC', micro_sign)
nfd = unicodedata.normalize('NFD', micro_sign)
nfkc = unicodedata.normalize('NFKC', micro_sign)
nfkd = unicodedata.normalize('NFKD', micro_sign)

print(f"\nUnicode normalization forms:")
print(f"  NFC:  '{nfc}' (U+{ord(nfc):04X})")
print(f"  NFD:  '{nfd}' (U+{ord(nfd):04X})")
print(f"  NFKC: '{nfkc}' (U+{ord(nfkc):04X}) ← Python uses this for identifiers!")
print(f"  NFKD: '{nfkd}' (U+{ord(nfkd):04X})")

# Show what happens in AST
print(f"\nPython AST behavior:")
parsed = ast.parse(micro_sign, mode='eval')
print(f"  ast.parse('{micro_sign}') creates ast.Name node")
print(f"  Name.id = '{parsed.body.id}' (U+{ord(parsed.body.id):04X})")

# This is the root cause
print(f"\nROOT CAUSE:")
print(f"  Python normalizes identifiers using NFKC (PEP 3131)")
print(f"  'µ' (U+00B5) is normalized to 'μ' (U+03BC)")
print(f"  This happens in ast.parse() when creating Name nodes")

# The fix would be to detect when the original string differs from the normalized version
print(f"\nPOTENTIAL FIX:")
print(f"  In _Replacement(), check if node.id differs from the original")
print(f"  If NFKC normalization changed it, treat as string literal instead")
print(f"  This preserves the original character representation")