import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators
import troposphere.ecr as ecr

print("Bug 1: Boolean validator accepts float 0.0 as False")
print("="*50)
try:
    result = validators.boolean(0.0)
    print(f"validators.boolean(0.0) = {result}")
    print(f"Type: {type(result)}")
    print("Expected: Should raise ValueError")
    print("Actual: Returns False")
except ValueError as e:
    print(f"Raised ValueError as expected: {e}")

print("\nBug 2: Boolean validator accepts float 1.0 as True")
print("="*50)
try:
    result = validators.boolean(1.0)
    print(f"validators.boolean(1.0) = {result}")
    print(f"Type: {type(result)}")
    print("Expected: Should raise ValueError")
    print("Actual: Returns True")
except ValueError as e:
    print(f"Raised ValueError as expected: {e}")

print("\nBug 3: Title validation rejects valid Unicode letters")
print("="*50)
# The character 'µ' is a valid Unicode lowercase letter (category Ll)
try:
    repo = ecr.Repository("µ")  # micro sign, Unicode category Ll (lowercase letter)
    print(f"Created repository with title 'µ'")
    print("This should work as 'µ' is a valid Unicode letter")
except ValueError as e:
    print(f"Rejected title 'µ': {e}")
    print("The regex ^[a-zA-Z0-9]+$ only matches ASCII, not Unicode letters")

print("\nAdditional test: Other Unicode letters")
print("="*50)
unicode_letters = ["π", "Δ", "λ", "ñ", "ü", "中"]
for char in unicode_letters:
    try:
        repo = ecr.Repository(char)
        print(f"✓ Accepted: '{char}'")
    except ValueError:
        print(f"✗ Rejected: '{char}'")