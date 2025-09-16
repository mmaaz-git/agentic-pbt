#!/usr/bin/env python3
import argcomplete
from argcomplete import split_line

# Test the failing case
print("Testing split_line word count...")
test_cases = [
    ['a'],
    ['hello'],
    ['hello', 'world'],
    ['a', 'b', 'c'],
]

for words_list in test_cases:
    line = ' '.join(words_list)
    result = split_line(line)
    prequote, prefix, suffix, words, wordbreak_pos = result
    print(f"Input: {words_list}")
    print(f"  Line: {line!r}")
    print(f"  Result: prequote={prequote!r}, prefix={prefix!r}, suffix={suffix!r}, words={words}, wordbreak_pos={wordbreak_pos}")
    print(f"  Expected word count: {len(words_list)}, Got: {len(words)}")
    print()

# Let's also test what happens at the end of input
print("Testing behavior at end of line...")
for line in ['a', 'hello', 'hello world', 'foo bar baz']:
    result = split_line(line)
    prequote, prefix, suffix, words, wordbreak_pos = result
    print(f"Line: {line!r}")
    print(f"  Words: {words}, prefix={prefix!r}, suffix={suffix!r}")
    
    # Also test with point at end
    result2 = split_line(line, len(line))
    prequote2, prefix2, suffix2, words2, wordbreak_pos2 = result2
    print(f"  With point={len(line)}: Words: {words2}, prefix={prefix2!r}, suffix={suffix2!r}")
    print()