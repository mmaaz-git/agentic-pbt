#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

# Test SplitMode which doesn't require a dictionary
from sudachipy import SplitMode

print("Testing SplitMode properties:")
print("=" * 60)

# Test class variables exist
print("SplitMode.A:", SplitMode.A)
print("SplitMode.B:", SplitMode.B)
print("SplitMode.C:", SplitMode.C)

# Test that they are distinct
print("\nUniqueness:")
print(f"A != B: {SplitMode.A != SplitMode.B}")
print(f"B != C: {SplitMode.B != SplitMode.C}")
print(f"A != C: {SplitMode.A != SplitMode.C}")

# Test string representation
print("\nString representations:")
print(f"str(SplitMode.A): {str(SplitMode.A)}")
print(f"str(SplitMode.B): {str(SplitMode.B)}")
print(f"str(SplitMode.C): {str(SplitMode.C)}")

# Test initialization from strings
print("\nInitialization from strings:")
try:
    # According to the pyi file, SplitMode.__init__ creates from strings
    mode_a = SplitMode("A")
    mode_b = SplitMode("b")  # lowercase should work
    mode_c = SplitMode("C")
    print("Initialization from strings works")
    print(f"SplitMode('A'): {mode_a}")
    print(f"SplitMode('b'): {mode_b}")
except Exception as e:
    print(f"Error: {e}")

# Test None defaults to C
print("\nNone defaults to C:")
try:
    mode_default = SplitMode(None)
    print(f"SplitMode(None): {mode_default}")
    print(f"Is it C? {mode_default == SplitMode.C}")
except Exception as e:
    print(f"Error: {e}")

# Test invalid inputs
print("\nInvalid inputs:")
for invalid in ["D", "abc", 123, "", "AA"]:
    try:
        invalid_mode = SplitMode(invalid)
        print(f"SplitMode({repr(invalid)}): {invalid_mode} - UNEXPECTED SUCCESS")
    except Exception as e:
        print(f"SplitMode({repr(invalid)}): {type(e).__name__}: {e}")