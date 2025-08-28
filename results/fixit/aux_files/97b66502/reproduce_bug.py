import sys
import re

# Add fixit to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import fixit.ftypes as ftypes

# The regex from ftypes.py
print("Testing LintIgnoreRegex bug...")
print("="*60)

# Test case that hypothesis found
test_cases = [
    "# lint-ignore: [",
    "# lint-fixme: [",
    "# lint-ignore: []",
    "# lint-ignore: [,",
    "# lint-ignore: a[b",
    "# lint-ignore: valid, [",
    "# lint-ignore: [valid",
]

for comment in test_cases:
    print(f"\nTesting: {repr(comment)}")
    match = ftypes.LintIgnoreRegex.search(comment)
    
    if match:
        groups = match.groups()
        print(f"  Matched! Groups: {groups}")
        print(f"  Directive: {groups[0]}")
        print(f"  Rule names: {groups[1]}")
        
        # Check if the regex captured the rule names correctly
        if ":" in comment:
            expected_names = comment.split(":", 1)[1].strip()
            if groups[1] != expected_names:
                print(f"  ⚠️  MISMATCH: Expected '{expected_names}', got '{groups[1]}'")
    else:
        print(f"  No match!")
        if ":" in comment:
            print(f"  ⚠️  ERROR: Should have matched but didn't!")

print("\n" + "="*60)
print("Detailed regex analysis:")
print(f"Regex pattern: {ftypes.LintIgnoreRegex.pattern}")

# Let's see what the regex actually matches
print("\n" + "="*60)
print("Understanding the regex behavior:")

# The regex expects word characters (\w+) for rule names
# But '[' is not a word character
print("\nThe regex rule name pattern: \\w+")
print("\\w matches: [a-zA-Z0-9_]")
print("'[' is not in this set, so it doesn't match as a rule name")

# Create a simpler test
simple_test = "# lint-ignore: ["
print(f"\nSimple test: {repr(simple_test)}")
match = ftypes.LintIgnoreRegex.search(simple_test)
if match:
    print(f"Groups: {match.groups()}")
else:
    print("No match!")

# What the regex actually captures
print("\n" + "="*60)
print("What the regex actually does:")
test_with_bracket = "# lint-ignore: [ some text"
match = ftypes.LintIgnoreRegex.search(test_with_bracket)
if match:
    print(f"Input: {repr(test_with_bracket)}")
    print(f"Full match: {repr(match.group(0))}")
    print(f"Groups: {match.groups()}")
    
# Analyze what happens: the regex stops matching at '['
print("\nConclusion: The regex pattern \\w+ for rule names cannot match")
print("special characters like '['. The regex will fail to capture")
print("the rule names portion when it starts with a non-word character.")