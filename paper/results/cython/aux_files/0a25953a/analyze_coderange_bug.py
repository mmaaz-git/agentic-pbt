"""
Deep dive into the CodeRange bug
"""

from Cython.Plex.Regexps import CodeRange, chars_to_ranges, Any

# The bug: chars_to_ranges merges adjacent characters incorrectly
print("=== The Bug ===")
print("chars_to_ranges('\t\t') incorrectly merges two tabs into a range that includes newline")
print()

# Test chars_to_ranges with duplicate characters
test_inputs = [
    '\t\t',      # Two tabs (code 9)
    '\t',        # One tab
    'aa',        # Two 'a's
    '\x08\x08',  # Two backspaces (code 8)
    '\x0b\x0b',  # Two vertical tabs (code 11)
]

for s in test_inputs:
    ranges = chars_to_ranges(s)
    print(f"chars_to_ranges({repr(s)}) = {ranges}")
    if len(ranges) == 2:
        start, end = ranges[0], ranges[1]
        print(f"  Range: [{start}, {end}) = chars {start} to {end-1}")
        if start <= 10 < end:
            print(f"  WARNING: Range includes newline (10)!")
    print()

print("=== Root Cause Analysis ===")
print("Looking at chars_to_ranges implementation (lines 28-48)...")
print()

# Manually trace the algorithm for '\t\t'
s = '\t\t'
char_list = list(s)
char_list.sort()  # ['	', '	']
print(f"Input: {repr(s)}")
print(f"After list and sort: {[repr(c) for c in char_list]}")
print()

i = 0
n = len(char_list)
result = []
print("Algorithm trace:")
while i < n:
    code1 = ord(char_list[i])
    print(f"  i={i}: code1 = ord('{repr(char_list[i])}') = {code1}")
    code2 = code1 + 1
    print(f"       code2 = {code1} + 1 = {code2}")
    i += 1
    print(f"       i += 1 -> i = {i}")
    
    # The bug is here! 
    while i < n and code2 >= ord(char_list[i]):
        print(f"  while i={i} < n={n} and code2={code2} >= ord('{repr(char_list[i])}')={ord(char_list[i])}:")
        code2 += 1  
        print(f"       code2 += 1 -> code2 = {code2}")
        i += 1
        print(f"       i += 1 -> i = {i}")
    
    result.append(code1)
    result.append(code2)
    print(f"  Append [{code1}, {code2})")
    print()

print(f"Final result: {result}")
print()
print("=== THE BUG ===")
print("When processing duplicate characters, the algorithm incorrectly extends")
print("the range by incrementing code2 even when the character is the same.")
print("For two tabs ('\\t\\t'), both have code 9:")
print("  - First tab: code1=9, code2=10")
print("  - Second tab is also 9, and 10 >= 9, so code2 becomes 11")
print("  - Final range is [9, 11) which includes newline (10)")
print()
print("The algorithm should recognize that duplicate characters don't extend the range!")