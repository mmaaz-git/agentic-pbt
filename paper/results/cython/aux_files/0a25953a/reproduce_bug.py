"""
Minimal reproduction of the Any() match_nl bug
"""

from Cython.Plex.Regexps import Any, chars_to_ranges, CodeRanges

# Test with tab character
chars = '\t'
any_re = Any(chars)

print(f"Input chars: {repr(chars)}")
print(f"any_re.match_nl: {any_re.match_nl}")
print(f"Expected: 0 (since \\t is not \\n)")
print()

# Let's trace through what Any() does
ranges = chars_to_ranges(chars)
print(f"chars_to_ranges('{repr(chars)}'): {ranges}")

# Any() calls CodeRanges
code_ranges_re = CodeRanges(ranges)
print(f"CodeRanges result match_nl: {code_ranges_re.match_nl}")
print()

# Let's check what CodeRanges does with the tab character
print("Tab character code:", ord('\t'))
print("Newline character code:", ord('\n'))
print()

# The issue seems to be in how CodeRanges handles the range
# Let's test different characters
test_chars = ['\t', ' ', 'a', '\r', '\x0b']
for ch in test_chars:
    test_re = Any(ch)
    print(f"Any('{repr(ch)}').match_nl = {test_re.match_nl} (expected: 0)")