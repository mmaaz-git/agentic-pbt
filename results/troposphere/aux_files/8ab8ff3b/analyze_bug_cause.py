#!/usr/bin/env python3
"""Analyze the root cause of the boolean validator bug."""

# Demonstrate the Python equality behavior that causes the bug
print("Python equality behavior that causes the bug:")
print(f"0.0 == 0: {0.0 == 0}")
print(f"1.0 == 1: {1.0 == 1}")
print(f"0.0 in [0]: {0.0 in [0]}")
print(f"1.0 in [1]: {1.0 in [1]}")

print("\nConsequence:")
print("The boolean validator unintentionally accepts float values 0.0 and 1.0")
print("because Python considers them equal to integers 0 and 1 respectively.")

print("\nCorrect behavior would be:")
print("- Accept: True, False, 0, 1, '0', '1', 'true', 'True', 'false', 'False'")  
print("- Reject: 0.0, 1.0, and all other float values")

print("\nProposed fix:")
print("Use explicit type checking in addition to value checking:")
print("""
def boolean(x: Any) -> bool:
    # Check exact types and values
    if x is True or (isinstance(x, int) and x == 1) or x in ["1", "true", "True"]:
        return True
    if x is False or (isinstance(x, int) and x == 0) or x in ["0", "false", "False"]:
        return False
    raise ValueError
""")