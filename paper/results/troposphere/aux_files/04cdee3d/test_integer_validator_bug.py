"""Focused test to investigate integer validator bug with infinity."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Test the integer validator with float('inf')
def test_integer_validator_with_infinity():
    """Test integer validator with infinity values."""
    
    print("Testing validators.integer() with float('inf')...")
    try:
        result = validators.integer(float('inf'))
        print(f"SUCCESS: validators.integer(float('inf')) returned: {result}")
    except ValueError as e:
        print(f"ValueError raised (expected): {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
    
    print("\nTesting validators.integer() with float('-inf')...")
    try:
        result = validators.integer(float('-inf'))
        print(f"SUCCESS: validators.integer(float('-inf')) returned: {result}")
    except ValueError as e:
        print(f"ValueError raised (expected): {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
    
    print("\nTesting validators.integer() with float('nan')...")
    try:
        result = validators.integer(float('nan'))
        print(f"SUCCESS: validators.integer(float('nan')) returned: {result}")
    except ValueError as e:
        print(f"ValueError raised (expected): {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
    
    # Compare with Python's int() behavior
    print("\n--- Python's int() behavior for comparison ---")
    
    print("Testing int(float('inf'))...")
    try:
        result = int(float('inf'))
        print(f"SUCCESS: int(float('inf')) returned: {result}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
    
    print("\nTesting int(float('-inf'))...")
    try:
        result = int(float('-inf'))
        print(f"SUCCESS: int(float('-inf')) returned: {result}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
    
    print("\nTesting int(float('nan'))...")
    try:
        result = int(float('nan'))
        print(f"SUCCESS: int(float('nan')) returned: {result}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_integer_validator_with_infinity()