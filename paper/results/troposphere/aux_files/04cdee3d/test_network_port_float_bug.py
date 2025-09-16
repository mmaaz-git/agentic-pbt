"""Investigate network_port validator behavior with float values."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

def test_network_port_with_floats():
    """Test network_port validator with float values."""
    
    print("Testing network_port with float values...")
    
    # Test with 80.5 (non-integer float)
    print("\nTest: validators.network_port(80.5)")
    try:
        result = validators.network_port(80.5)
        print(f"SUCCESS: Returned {result} (type: {type(result)})")
        print(f"Converting to int: int(80.5) = {int(80.5)}")
    except ValueError as e:
        print(f"ValueError raised: {e}")
    except Exception as e:
        print(f"Other exception: {type(e).__name__}: {e}")
    
    # Test with 80.0 (integer-valued float)
    print("\nTest: validators.network_port(80.0)")
    try:
        result = validators.network_port(80.0)
        print(f"SUCCESS: Returned {result} (type: {type(result)})")
        print(f"Converting to int: int(80.0) = {int(80.0)}")
    except ValueError as e:
        print(f"ValueError raised: {e}")
    except Exception as e:
        print(f"Other exception: {type(e).__name__}: {e}")
    
    # Test with 65535.5 (boundary + 0.5)
    print("\nTest: validators.network_port(65535.5)")
    try:
        result = validators.network_port(65535.5)
        print(f"SUCCESS: Returned {result} (type: {type(result)})")
        print(f"Converting to int: int(65535.5) = {int(65535.5)}")
    except ValueError as e:
        print(f"ValueError raised: {e}")
    except Exception as e:
        print(f"Other exception: {type(e).__name__}: {e}")
    
    # Test with 65536.0 (just over boundary)
    print("\nTest: validators.network_port(65536.0)")
    try:
        result = validators.network_port(65536.0)
        print(f"SUCCESS: Returned {result} (type: {type(result)})")
        print(f"Converting to int: int(65536.0) = {int(65536.0)}")
    except ValueError as e:
        print(f"ValueError raised: {e}")
    except Exception as e:
        print(f"Other exception: {type(e).__name__}: {e}")
    
    # Look at what integer() does with these values
    print("\n--- Testing underlying integer() validator ---")
    
    print("\nTest: validators.integer(80.5)")
    try:
        result = validators.integer(80.5)
        print(f"SUCCESS: Returned {result}")
    except ValueError as e:
        print(f"ValueError raised: {e}")
    
    print("\nTest: validators.integer(80.0)")
    try:
        result = validators.integer(80.0)
        print(f"SUCCESS: Returned {result}")
    except ValueError as e:
        print(f"ValueError raised: {e}")
    
    # Check Python's int() behavior
    print("\n--- Python's int() behavior ---")
    print(f"int(80.5) = {int(80.5)}")
    print(f"int(80.0) = {int(80.0)}")


if __name__ == "__main__":
    test_network_port_with_floats()