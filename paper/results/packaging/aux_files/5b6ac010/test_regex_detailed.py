import re

# The actual regex pattern from packaging.utils
pattern = r'^([a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])$'
regex = re.compile(pattern)

# Test and show match groups
test_cases = ['0--0', 'a--b', 'foo--bar']

for test in test_cases:
    match = regex.match(test)
    if match:
        print(f'{test!r}: MATCH')
        print(f'  Full match: {match.group(0)!r}')
        print(f'  Groups: {match.groups()}')
    else:
        print(f'{test!r}: NO MATCH')
    print()

# Let's trace through '0--0' manually
print("Manual analysis of '0--0':")
print("Pattern: ^([a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])$")
print()

# Try different interpretations
print("Testing if the entire string '0--0' matches the first alternative [a-z0-9]:")
print("  No, '0--0' is 4 characters, not 1")
print()

print("Testing if '0--0' matches the second alternative:")
print("  [a-z0-9]([a-z0-9-](?!--))*[a-z0-9]")
print("  Start: '0' matches [a-z0-9]")
print("  Middle: '--0' should match ([a-z0-9-](?!--))*[a-z0-9]")
print("  But the negative lookahead (?!--) should prevent matching '--'")
print()

# Test what actually happens with the middle part
middle_pattern = r'([a-z0-9-](?!--))*'
middle_regex = re.compile(middle_pattern)
test_middles = ['-', '--', '-0', '--0']
for middle in test_middles:
    match = middle_regex.match(middle)
    print(f"  Middle pattern on {middle!r}: {match.group(0) if match else 'NO MATCH'}")