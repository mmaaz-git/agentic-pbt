#!/usr/bin/env python3
"""Minimal reproduction of the _escape bug in sphinxcontrib.htmlhelp"""

import sys
import re
import html
from html.entities import codepoint2name

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')
import sphinxcontrib.htmlhelp as htmlhelp

# Test character U+0091 (Private Use One)
test_char = '\x91'
print(f"Testing character: U+{ord(test_char):04X} (decimal {ord(test_char)})")

# Apply the _escape function as the HTMLHelpBuilder does
builder = htmlhelp.HTMLHelpBuilder
escaped = re.sub(r"[^\x00-\x7F]", builder._escape, test_char)
print(f"Escaped result: {escaped}")

# Unescape the result
unescaped = html.unescape(escaped)
print(f"Unescaped result: {unescaped!r} (U+{ord(unescaped):04X})")

# Check if round-trip works
print(f"Original character: {test_char!r} (U+{ord(test_char):04X})")
print(f"Round-trip successful: {test_char == unescaped}")

if test_char != unescaped:
    print(f"\nBUG FOUND: Character U+{ord(test_char):04X} is incorrectly escaped")
    print(f"  Expected: Character should round-trip correctly")
    print(f"  Actual: U+{ord(test_char):04X} -> {escaped} -> U+{ord(unescaped):04X} ('{unescaped}')")
    
# Let's check what's in codepoint2name for this character
print(f"\nIs U+0091 in codepoint2name? {145 in codepoint2name}")
print(f"Is U+2018 in codepoint2name? {0x2018 in codepoint2name}")

# Check the HTML standard
print("\nHTML5 spec says character references 0x80-0x9F map to Windows-1252:")
print("  U+0091 (145) should map to U+2018 (LEFT SINGLE QUOTATION MARK)")
print("  This is a known HTML parsing quirk for legacy reasons")