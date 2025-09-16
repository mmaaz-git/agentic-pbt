"""
Proposed fix for the chars_to_ranges bug
"""

def chars_to_ranges_buggy(s):
    """
    BUGGY VERSION - Current implementation
    """
    char_list = list(s)
    char_list.sort()
    i = 0
    n = len(char_list)
    result = []
    while i < n:
        code1 = ord(char_list[i])
        code2 = code1 + 1
        i += 1
        while i < n and code2 >= ord(char_list[i]):
            code2 += 1  # BUG: Increments even for duplicate chars
            i += 1
        result.append(code1)
        result.append(code2)
    return result


def chars_to_ranges_fixed(s):
    """
    FIXED VERSION - Correctly handles duplicates
    """
    char_list = list(s)
    char_list.sort()
    i = 0
    n = len(char_list)
    result = []
    while i < n:
        code1 = ord(char_list[i])
        code2 = code1 + 1
        i += 1
        while i < n and code2 >= ord(char_list[i]):
            # Only increment code2 if we see a NEW character in sequence
            if ord(char_list[i]) >= code2:
                code2 = ord(char_list[i]) + 1
            i += 1
        result.append(code1)
        result.append(code2)
    return result


# Test both versions
test_cases = [
    '\t\t',      # Two tabs - the failing case
    '\t',        # Single tab
    'abc',       # Sequential chars
    'aac',       # Mixed with duplicate
    'aaa',       # All duplicates
    '\x08\x08',  # Two backspaces
    'abcd',      # Sequential
]

print("Comparing buggy vs fixed implementation:\n")
print(f"{'Input':<15} {'Buggy Result':<20} {'Fixed Result':<20} {'Includes \\n?'}")
print("-" * 70)

for s in test_cases:
    buggy = chars_to_ranges_buggy(s)
    fixed = chars_to_ranges_fixed(s)
    
    # Check if buggy version includes newline
    includes_newline = False
    for i in range(0, len(buggy), 2):
        if buggy[i] <= 10 < buggy[i+1]:
            includes_newline = True
            break
    
    print(f"{repr(s):<15} {str(buggy):<20} {str(fixed):<20} {'YES (BUG!)' if includes_newline else 'No'}")