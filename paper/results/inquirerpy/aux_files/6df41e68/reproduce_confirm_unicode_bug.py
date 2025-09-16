#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.prompts import ConfirmPrompt

print("Testing ConfirmPrompt Unicode character handling...")
print()

# Test case: German eszett character
print("Test case: Using German eszett (ß) as reject_letter")
print("  confirm_letter: 'y'")
print("  reject_letter: 'ß'")
print()

try:
    prompt = ConfirmPrompt(
        message="Test",
        confirm_letter='y',
        reject_letter='ß'
    )
    print("  SUCCESS: Prompt created without error")
except ValueError as e:
    print(f"  ERROR: {e}")
    print()
    print("Root cause analysis:")
    print("  The letter 'ß' uppercases to 'SS' in German")
    print("  Python: 'ß'.upper() =", repr('ß'.upper()))
    print("  The key binding system tries to parse 'SS' as a single key")
    print("  but it's actually two characters, causing the error")
    print()
    print("This is a bug because:")
    print("  1. The user provided a single character as required")
    print("  2. The prompt internally calls .upper() on it (line 125 in confirm.py)")
    print("  3. Some unicode characters expand when uppercased")
    print("  4. The key binding system can't handle multi-char keys")

print()
print("="*60)
print()

# Test more problematic Unicode characters
print("Other problematic Unicode characters that expand when uppercased:")
problematic_chars = [
    ('ß', 'SS'),  # German eszett
    ('ı', 'I'),   # Turkish dotless i (might work but different char)
    ('ﬀ', 'FF'),  # Latin small ligature ff
    ('ﬁ', 'FI'),  # Latin small ligature fi
    ('ﬂ', 'FL'),  # Latin small ligature fl
    ('ﬃ', 'FFI'), # Latin small ligature ffi
    ('ﬄ', 'FFL'), # Latin small ligature ffl
    ('ﬅ', 'ST'),  # Latin small ligature st
    ('ﬆ', 'ST'),  # Latin small ligature st (alternative)
]

for char, upper in problematic_chars:
    print(f"  '{char}' -> '{char.upper()}' (expected: {upper})")
    if len(char.upper()) > 1:
        try:
            prompt = ConfirmPrompt(
                message="Test",
                confirm_letter='y',
                reject_letter=char
            )
            print(f"    Unexpected: '{char}' did NOT cause an error")
        except ValueError:
            print(f"    Confirmed: '{char}' causes ValueError")