#!/usr/bin/env python3
"""
Focused tests to find specific bugs in troposphere.mediatailor
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.validators as validators

def test_boolean_edge_cases():
    """Test the boolean validator with edge cases"""
    print("Testing boolean validator edge cases...")
    
    # These should work according to the code
    test_cases = [
        # (input, expected_output)
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        ("1", True),
        ("0", False),
        ("true", True),
        ("false", False),
        ("True", True),
        ("False", False),
    ]
    
    for input_val, expected in test_cases:
        try:
            result = validators.boolean(input_val)
            if result != expected:
                print(f"BUG: boolean({input_val!r}) returned {result}, expected {expected}")
            else:
                print(f"OK: boolean({input_val!r}) = {result}")
        except Exception as e:
            print(f"BUG: boolean({input_val!r}) raised {e}")
    
    # Edge cases that might reveal bugs
    edge_cases = [
        # The code checks for specific values, what about variations?
        "TRUE",  # All caps
        "FALSE", # All caps
        "tRuE",  # Mixed case
        "fAlSe", # Mixed case
        " true", # Leading space
        "true ", # Trailing space
        "1.0",   # String float that equals 1
        "0.0",   # String float that equals 0
        1.0,     # Float that equals 1
        0.0,     # Float that equals 0
    ]
    
    print("\nTesting edge cases that might fail...")
    for val in edge_cases:
        try:
            result = validators.boolean(val)
            print(f"UNEXPECTED: boolean({val!r}) = {result} (should this work?)")
        except ValueError:
            print(f"boolean({val!r}) raised ValueError")
        except Exception as e:
            print(f"boolean({val!r}) raised {type(e).__name__}: {e}")


def test_integer_float_edge_cases():
    """Test integer validator with float edge cases"""
    print("\n" + "="*50)
    print("Testing integer validator with floats...")
    
    # Floats that are mathematically integers
    float_integers = [1.0, 2.0, -3.0, 0.0, 100.0]
    
    for val in float_integers:
        try:
            result = validators.integer(val)
            print(f"integer({val!r}) = {result}")
            # Verify it's actually valid
            int_val = int(result)
            print(f"  Converts to int: {int_val}")
        except ValueError as e:
            print(f"BUG? integer({val!r}) raised ValueError: {e}")
            print(f"  But {val} == {int(val)}, so it's a valid integer!")
    
    # Test with very large floats
    large_floats = [1e20, -1e20, 1e100]
    print("\nTesting with large floats...")
    for val in large_floats:
        try:
            result = validators.integer(val)
            print(f"integer({val!r}) = {result}")
        except Exception as e:
            print(f"integer({val!r}) raised {type(e).__name__}: {e}")


def test_property_validation_bugs():
    """Test for bugs in property validation"""
    print("\n" + "="*50)
    print("Testing property validation...")
    
    import troposphere.mediatailor as mediatailor
    
    # Test 1: Can we bypass required validation?
    print("\n1. Testing required property bypass...")
    try:
        channel = mediatailor.Channel("Test")
        # Try to get dict without validation
        dict_no_validation = channel.to_dict(validation=False)
        print(f"SUCCESS: Got dict without validation: {list(dict_no_validation.keys())}")
        
        # Now try with validation (should fail)
        dict_with_validation = channel.to_dict(validation=True)
        print(f"BUG: Got dict WITH validation (should have failed): {dict_with_validation}")
    except ValueError as e:
        print(f"Validation correctly raised ValueError: {e}")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
    
    # Test 2: What happens with None values for required fields?
    print("\n2. Testing None for required fields...")
    try:
        output = mediatailor.RequestOutputItem(
            ManifestName=None,  # Required but None
            SourceGroup=None    # Required but None
        )
        dict_repr = output.to_dict()
        print(f"BUG: Created RequestOutputItem with None required fields: {dict_repr}")
    except Exception as e:
        print(f"Correctly rejected None: {type(e).__name__}: {e}")
    
    # Test 3: Empty strings for required fields
    print("\n3. Testing empty strings for required fields...")
    try:
        output = mediatailor.RequestOutputItem(
            ManifestName="",  # Required but empty
            SourceGroup=""    # Required but empty
        )
        dict_repr = output.to_dict()
        print(f"Created RequestOutputItem with empty strings: {dict_repr}")
        # This might be allowed, but is it correct behavior?
    except Exception as e:
        print(f"Rejected empty strings: {type(e).__name__}: {e}")
    
    # Test 4: Wrong types for typed fields
    print("\n4. Testing wrong types...")
    try:
        settings = mediatailor.DashPlaylistSettings(
            ManifestWindowSeconds="not a number"  # Should be double
        )
        dict_repr = settings.to_dict()
        print(f"BUG: Accepted string for double field: {dict_repr}")
    except Exception as e:
        print(f"Correctly rejected wrong type: {type(e).__name__}: {e}")


def test_equality_and_hash():
    """Test __eq__ and __hash__ implementations"""
    print("\n" + "="*50)
    print("Testing equality and hash...")
    
    import troposphere.mediatailor as mediatailor
    
    # Create two identical objects
    output1 = mediatailor.RequestOutputItem(
        ManifestName="test",
        SourceGroup="source"
    )
    output2 = mediatailor.RequestOutputItem(
        ManifestName="test",
        SourceGroup="source"
    )
    
    print(f"output1 == output2: {output1 == output2}")
    print(f"hash(output1) == hash(output2): {hash(output1) == hash(output2)}")
    
    # Python contract: if a == b, then hash(a) == hash(b)
    if output1 == output2 and hash(output1) != hash(output2):
        print("BUG: Equal objects have different hashes!")
    
    # Test with different objects
    output3 = mediatailor.RequestOutputItem(
        ManifestName="different",
        SourceGroup="source"
    )
    print(f"output1 == output3: {output1 == output3}")
    print(f"hash(output1) == hash(output3): {hash(output1) == hash(output3)}")


if __name__ == "__main__":
    test_boolean_edge_cases()
    test_integer_float_edge_cases()
    test_property_validation_bugs()
    test_equality_and_hash()