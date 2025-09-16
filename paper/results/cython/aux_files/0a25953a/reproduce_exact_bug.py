"""
Exact reproduction of the failing test case
"""

from Cython.Plex.Regexps import Any, chars_to_ranges, CodeRanges, CodeRange

# Exact failing input from hypothesis
chars = '\t\t'
any_re = Any(chars)

print(f"Input chars: {repr(chars)}")
print(f"any_re.match_nl: {any_re.match_nl}")
print(f"Expected: 0 (since tabs are not newlines)")
print()

# Trace through the Any() function
ranges = chars_to_ranges(chars)
print(f"chars_to_ranges({repr(chars)}): {ranges}")
print()

# Check what CodeRanges does
import Cython.Plex.Regexps as Regexps

# Manually trace CodeRanges function from line 79-85
code_list = ranges
re_list = []
for i in range(0, len(code_list), 2):
    code_range = CodeRange(code_list[i], code_list[i + 1])
    print(f"CodeRange({code_list[i]}, {code_list[i + 1]}) -> match_nl = {code_range.match_nl}")
    re_list.append(code_range)

from Cython.Plex.Regexps import Alt
result = Alt(*re_list)
print(f"\nAlt of CodeRanges -> match_nl = {result.match_nl}")

# The issue is that CodeRange(9, 11) includes newline (10)!
print("\n--- Analysis ---")
print(f"Tab code: {ord('\t')} = 9")
print(f"Newline code: {ord('\n')} = 10")
print(f"chars_to_ranges('\t\t') returns [9, 10]")
print(f"But this creates CodeRange(9, 10) which is [9, 10)")
print(f"This range does NOT include newline (10), so why match_nl=1?")