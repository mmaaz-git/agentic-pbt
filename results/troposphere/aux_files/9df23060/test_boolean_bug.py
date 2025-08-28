"""Test for boolean() function case sensitivity issue"""

import troposphere.ssmcontacts as ssmcontacts

print("Boolean function case sensitivity test:")
print("-" * 40)

# These work
print("Working cases:")
for val in ['true', 'True', 'false', 'False']:
    result = ssmcontacts.boolean(val)
    print(f"  boolean('{val}') = {result}")

# These should work but don't (case variations)
print("\nFailing cases (should work for case-insensitive boolean):")
test_cases = ['TRUE', 'FALSE', 'tRue', 'fAlSe']
for val in test_cases:
    try:
        result = ssmcontacts.boolean(val)
        print(f"  boolean('{val}') = {result}")
    except ValueError:
        print(f"  boolean('{val}') = ValueError (should accept case variations)")

print("\nProblem: Common boolean string variations are rejected")
print("Users expect 'TRUE', 'FALSE' etc. to work like 'true', 'false'")