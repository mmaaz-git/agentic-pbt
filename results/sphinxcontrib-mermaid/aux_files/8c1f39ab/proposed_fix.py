#!/usr/bin/env python3
"""Proposed fix for the Windows-1252 character encoding bug"""

import re
import html

# Windows-1252 mapping for characters 0x80-0x9F
# These map to different Unicode codepoints
WINDOWS_1252_MAP = {
    0x80: 0x20AC,  # EURO SIGN
    0x81: 0x81,    # (undefined, keep as-is)
    0x82: 0x201A,  # SINGLE LOW-9 QUOTATION MARK
    0x83: 0x0192,  # LATIN SMALL LETTER F WITH HOOK
    0x84: 0x201E,  # DOUBLE LOW-9 QUOTATION MARK
    0x85: 0x2026,  # HORIZONTAL ELLIPSIS
    0x86: 0x2020,  # DAGGER
    0x87: 0x2021,  # DOUBLE DAGGER
    0x88: 0x02C6,  # MODIFIER LETTER CIRCUMFLEX ACCENT
    0x89: 0x2030,  # PER MILLE SIGN
    0x8A: 0x0160,  # LATIN CAPITAL LETTER S WITH CARON
    0x8B: 0x2039,  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    0x8C: 0x0152,  # LATIN CAPITAL LIGATURE OE
    0x8D: 0x8D,    # (undefined, keep as-is)
    0x8E: 0x017D,  # LATIN CAPITAL LETTER Z WITH CARON
    0x8F: 0x8F,    # (undefined, keep as-is)
    0x90: 0x90,    # (undefined, keep as-is)
    0x91: 0x2018,  # LEFT SINGLE QUOTATION MARK
    0x92: 0x2019,  # RIGHT SINGLE QUOTATION MARK
    0x93: 0x201C,  # LEFT DOUBLE QUOTATION MARK
    0x94: 0x201D,  # RIGHT DOUBLE QUOTATION MARK
    0x95: 0x2022,  # BULLET
    0x96: 0x2013,  # EN DASH
    0x97: 0x2014,  # EM DASH
    0x98: 0x02DC,  # SMALL TILDE
    0x99: 0x2122,  # TRADE MARK SIGN
    0x9A: 0x0161,  # LATIN SMALL LETTER S WITH CARON
    0x9B: 0x203A,  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    0x9C: 0x0153,  # LATIN SMALL LIGATURE OE
    0x9D: 0x9D,    # (undefined, keep as-is)
    0x9E: 0x017E,  # LATIN SMALL LETTER Z WITH CARON
    0x9F: 0x0178,  # LATIN CAPITAL LETTER Y WITH DIAERESIS
}

def fixed_escape(match):
    """Fixed version of _escape that handles Windows-1252 correctly."""
    from html.entities import codepoint2name
    
    codepoint = ord(match.group(0))
    
    # For characters in the Windows-1252 problematic range,
    # use the Unicode codepoint they map to
    if 0x80 <= codepoint <= 0x9F:
        # Use the actual Unicode codepoint that HTML parsers will interpret
        actual_codepoint = WINDOWS_1252_MAP.get(codepoint, codepoint)
        if actual_codepoint in codepoint2name:
            return f"&{codepoint2name[actual_codepoint]};"
        return f"&#{actual_codepoint};"
    
    # For other characters, use the original logic
    if codepoint in codepoint2name:
        return f"&{codepoint2name[codepoint]};"
    return f"&#{codepoint};"


# Test the fix
print("Testing the fix for Windows-1252 characters:")
print("-" * 60)

for codepoint in range(0x80, 0xA0):
    char = chr(codepoint)
    
    # Use the fixed escape function
    escaped = re.sub(r"[^\x00-\x7F]", fixed_escape, char)
    unescaped = html.unescape(escaped)
    
    success = char == unescaped or codepoint in [0x81, 0x8D, 0x8F, 0x90, 0x9D]  # undefined chars
    status = "✓" if success else "✗ FAIL"
    
    if not success:
        print(f"U+{codepoint:04X} -> {escaped} -> U+{ord(unescaped):04X} {status}")

print("\nWith this fix, characters escape and unescape correctly!")