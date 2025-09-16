#!/usr/bin/env python3
"""Test all characters in the Windows-1252 problematic range"""

import sys
import re
import html
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')
import sphinxcontrib.htmlhelp as htmlhelp

builder = htmlhelp.HTMLHelpBuilder

print("Testing characters in range U+0080 to U+009F:")
print("These are C1 control characters that HTML parsers remap via Windows-1252")
print("-" * 60)

failures = []
for codepoint in range(0x80, 0xA0):
    char = chr(codepoint)
    escaped = re.sub(r"[^\x00-\x7F]", builder._escape, char)
    unescaped = html.unescape(escaped)
    
    if char != unescaped:
        failures.append((codepoint, escaped, ord(unescaped)))
        print(f"U+{codepoint:04X} -> {escaped} -> U+{ord(unescaped):04X} {'✗ FAIL' if char != unescaped else '✓'}")

print(f"\nFound {len(failures)} characters that don't round-trip correctly")
print("This is a known issue with HTML entity parsing and Windows-1252 legacy behavior")