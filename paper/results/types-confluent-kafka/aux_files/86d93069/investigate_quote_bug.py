"""Investigate the quote tracking bug in skip_line"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.parse import skip_line

# Test the specific failing case
print("Testing quote state transitions:")

# Test case 1: Start triple quote
line1 = '"""hello'
skip1, quote1 = skip_line(line1, "", 0, ())
print(f"Line: {repr(line1)}")
print(f"  Initial quote: ''")
print(f"  Final quote: {repr(quote1)}")
print(f"  Should skip: {skip1}")
print()

# Test case 2: Line with ending triple quote (THE FAILING CASE)
line2 = 'world"""'
skip2, quote2 = skip_line(line2, "", 0, ())
print(f"Line: {repr(line2)}")
print(f"  Initial quote: ''")
print(f"  Final quote: {repr(quote2)}")
print(f"  Expected: ''")
print(f"  Should skip: {skip2}")
print()

# Test continuing from triple quote state
line3 = 'world"""'
skip3, quote3 = skip_line(line3, '"""', 1, ())
print(f"Line: {repr(line3)} with initial quote: '\"\"\"'")
print(f"  Final quote: {repr(quote3)}")
print(f"  Expected: '' (should close the triple quote)")
print(f"  Should skip: {skip3}")
print()

# More detailed test
print("\nDetailed analysis of quote tracking:")

# When we start with empty quote and see triple quote at beginning
test1 = '"""test'
s1, q1 = skip_line(test1, "", 0, ())
print(f"1. '{test1}' -> quote={repr(q1)} (enters triple quote)")

# When we start with empty quote and see triple quote at end
test2 = 'test"""'
s2, q2 = skip_line(test2, "", 0, ())
print(f"2. '{test2}' -> quote={repr(q2)} (should it enter or not?)")

# When in triple quote and see closing triple quote
test3 = 'test"""more'
s3, q3 = skip_line(test3, '"""', 0, ())
print(f"3. '{test3}' in triple quote -> quote={repr(q3)} (should exit)")

# Edge case: just triple quotes
test4 = '"""'
s4, q4 = skip_line(test4, "", 0, ())
print(f"4. '{test4}' -> quote={repr(q4)}")

test5 = '""""""'  # Two triple quotes
s5, q5 = skip_line(test5, "", 0, ())
print(f"5. '{test5}' -> quote={repr(q5)}")

# Test the actual logic
print("\nAnalyzing skip_line logic for: 'world\"\"\"'")
line = 'world"""'
in_quote = ""
char_index = 0

print(f"Starting: in_quote={repr(in_quote)}, line={repr(line)}")
while char_index < len(line):
    print(f"  char_index={char_index}, char={repr(line[char_index])}, in_quote={repr(in_quote)}")
    
    if line[char_index] == "\\":
        print(f"    Found backslash, skipping next char")
        char_index += 1
    elif in_quote:
        if line[char_index : char_index + len(in_quote)] == in_quote:
            print(f"    Found closing quote, exiting quote")
            in_quote = ""
    elif line[char_index] in ("'", '"'):
        long_quote = line[char_index : char_index + 3]
        if long_quote in ('"""', "'''"):
            in_quote = long_quote
            char_index += 2
            print(f"    Found triple quote {repr(long_quote)}, entering, jumping to index {char_index + 1}")
        else:
            in_quote = line[char_index]
            print(f"    Found single quote {repr(line[char_index])}, entering")
    elif line[char_index] == "#":
        print(f"    Found comment, breaking")
        break
    
    char_index += 1

print(f"Final: in_quote={repr(in_quote)}")