"""
Minimal reproduction of boolean validator bug with complex numbers
"""

import troposphere.validators

# Test cases showing the bug
test_cases = [
    complex(0, 0),  # 0j
    complex(1, 0),  # 1+0j
    0j,
    1+0j,
    0.0+0j,
    1.0+0j,
]

print("Boolean validator incorrectly accepts complex numbers:")
print("=" * 50)

for value in test_cases:
    try:
        result = troposphere.validators.boolean(value)
        print(f"boolean({value!r}) = {result!r}")
        print(f"  -> BUG: Complex number accepted as boolean!")
    except ValueError as e:
        print(f"boolean({value!r}) -> ValueError (correct)")

print("\n" + "=" * 50)
print("Root cause analysis:")
print(f"0j == 0: {0j == 0}")
print(f"0j == False: {0j == False}")
print(f"1+0j == 1: {(1+0j) == 1}")  
print(f"1+0j == True: {(1+0j) == True}")

print("\nThe validator uses '==' comparison which allows complex numbers")
print("to match integer values when the imaginary part is zero.")

# Show the actual validator code issue
print("\nValidator code snippet:")
print("  if x in [True, 1, '1', 'true', 'True']:")
print("  if x in [False, 0, '0', 'false', 'False']:")
print("\nPython's 'in' operator uses '==' for comparison, so:")
print(f"  0j in [False, 0]: {0j in [False, 0]}")
print(f"  1+0j in [True, 1]: {(1+0j) in [True, 1]}")