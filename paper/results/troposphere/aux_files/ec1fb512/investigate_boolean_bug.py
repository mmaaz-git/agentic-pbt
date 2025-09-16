import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Test the boolean validator with various numeric types
test_values = [
    (0, "integer 0"),
    (1, "integer 1"),
    (0.0, "float 0.0"),
    (1.0, "float 1.0"),
    (0.5, "float 0.5"),
    (True, "bool True"),
    (False, "bool False"),
]

print("Testing boolean validator with numeric values:")
print("=" * 60)

for value, description in test_values:
    try:
        result = validators.boolean(value)
        print(f"{description:20} -> {result:5} (type: {type(value).__name__})")
    except ValueError:
        print(f"{description:20} -> ValueError raised")

print("\nLooking at the implementation:")
print("=" * 60)
print("The validator checks if x in [True, 1, '1', 'true', 'True']")
print("and if x in [False, 0, '0', 'false', 'False']")
print("\nThe issue: Python's equality comparison makes 1.0 == 1 and 0.0 == 0")
print("So 1.0 in [1] returns True, and 0.0 in [0] returns True")
print("\nDemonstration:")
print(f"1.0 == 1: {1.0 == 1}")
print(f"0.0 == 0: {0.0 == 0}")
print(f"1.0 in [1]: {1.0 in [1]}")
print(f"0.0 in [0]: {0.0 in [0]}")
print(f"0.5 in [0]: {0.5 in [0]}")