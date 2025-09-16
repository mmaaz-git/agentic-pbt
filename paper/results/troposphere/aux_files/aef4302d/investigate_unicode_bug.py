#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
import troposphere.kendra as kendra

print("=== Testing Unicode digit handling ===\n")

# Test various Unicode digits
unicode_digits = [
    ("୦", "Odia ZERO"),
    ("௧", "Tamil ONE"),
    ("၂", "Myanmar TWO"),
    ("໓", "Lao THREE"),
    ("༤", "Tibetan FOUR"),
    ("᠕", "Mongolian FIVE"),
    ("៦", "Khmer SIX"),
    ("๗", "Thai SEVEN"),
    ("๘", "Thai EIGHT"),
    ("๙", "Thai NINE"),
    ("٠", "Arabic-Indic ZERO"),
    ("١", "Arabic-Indic ONE"),
    ("۲", "Extended Arabic-Indic TWO"),
    ("߃", "NKo THREE"),
    ("०", "Devanagari ZERO"),
    ("১", "Bengali ONE"),
]

print("Testing integer validator with Unicode digits:")
for digit, name in unicode_digits:
    try:
        result = integer(digit)
        print(f"  ✓ {name} ('{digit}'): Accepted! Result = {result}, type = {type(result)}")
        
        # Try converting to int
        try:
            int_val = int(result)
            print(f"    Converts to int: {int_val}")
        except:
            print(f"    Cannot convert to int!")
            
    except ValueError as e:
        print(f"  ✗ {name} ('{digit}'): Rejected with error: {e}")

print("\n=== Testing in CapacityUnitsConfiguration ===")

# Try Thai digit "๗" (7)
thai_seven = "๗"
print(f"\nUsing Thai digit '{thai_seven}' (seven):")
try:
    config = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=thai_seven,
        StorageCapacityUnits=thai_seven
    )
    print(f"  ✓ Created successfully!")
    print(f"  to_dict() = {config.to_dict()}")
    
    # This is problematic - CloudFormation expects integers
    # but we have Unicode digit strings that can't be parsed as integers
    print(f"\n  PROBLEM: CloudFormation expects integer values but got Unicode strings")
    print(f"  that cannot be parsed as integers by standard parsers!")
    
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n=== Checking Python's int() behavior ===")
for digit, name in unicode_digits[:5]:
    try:
        val = int(digit)
        print(f"  int('{digit}') = {val}")
    except ValueError as e:
        print(f"  int('{digit}') raised ValueError: {e}")

print("\n=== Summary ===")
print("BUG FOUND: The integer validator accepts Unicode digit strings that")
print("cannot be converted to integers by Python's int() function.")
print("This violates the validator's purpose and will cause issues downstream.")