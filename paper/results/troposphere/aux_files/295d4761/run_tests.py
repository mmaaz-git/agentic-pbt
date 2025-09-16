#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import and run a simple test manually
import troposphere.validators as validators

print("Testing boolean validator...")

# Test valid inputs
test_cases_valid = [True, False, 1, 0, "true", "True", "false", "False", "1", "0"]
for val in test_cases_valid:
    try:
        result = validators.boolean(val)
        print(f"  boolean({val!r}) = {result}")
    except Exception as e:
        print(f"  boolean({val!r}) raised {e}")

print("\nTesting invalid inputs...")
test_cases_invalid = ["yes", "no", 2, -1, None, [], {}, "TRUE", "FALSE"]
for val in test_cases_invalid:
    try:
        result = validators.boolean(val)
        print(f"  boolean({val!r}) = {result} (UNEXPECTED SUCCESS)")
    except ValueError:
        print(f"  boolean({val!r}) raised ValueError (expected)")
    except Exception as e:
        print(f"  boolean({val!r}) raised {e}")

print("\n" + "="*50)
print("Testing integer validator...")

# Test the integer validator
test_ints = [0, 1, -1, 100, "123", "-456", 1.0, 2.0]
for val in test_ints:
    try:
        result = validators.integer(val)
        print(f"  integer({val!r}) = {result}")
    except Exception as e:
        print(f"  integer({val!r}) raised {e}")

print("\nTesting invalid integers...")
test_invalid_ints = [1.5, "abc", None, [], {}, "1.5"]
for val in test_invalid_ints:
    try:
        result = validators.integer(val)
        print(f"  integer({val!r}) = {result} (UNEXPECTED SUCCESS)")
    except ValueError as e:
        print(f"  integer({val!r}) raised ValueError: {e}")

print("\n" + "="*50)
print("Testing double validator...")

test_doubles = [0, 1.5, -2.7, "3.14", "1e10", 100]
for val in test_doubles:
    try:
        result = validators.double(val)
        print(f"  double({val!r}) = {result}")
    except Exception as e:
        print(f"  double({val!r}) raised {e}")

print("\nTesting invalid doubles...")
test_invalid_doubles = ["abc", None, [], {}]
for val in test_invalid_doubles:
    try:
        result = validators.double(val)
        print(f"  double({val!r}) = {result} (UNEXPECTED SUCCESS)")
    except ValueError as e:
        print(f"  double({val!r}) raised ValueError: {e}")

print("\n" + "="*50)
print("Testing Channel class...")

import troposphere.mediatailor as mediatailor

# Test creating a channel with required properties
try:
    output = mediatailor.RequestOutputItem(
        ManifestName="test",
        SourceGroup="test"
    )
    channel = mediatailor.Channel(
        "TestChannel",
        ChannelName="MyChannel",
        PlaybackMode="LOOP",
        Outputs=[output]
    )
    print("  Created Channel successfully")
    dict_repr = channel.to_dict()
    print(f"  Channel.to_dict() succeeded, keys: {list(dict_repr.keys())}")
except Exception as e:
    print(f"  Failed to create Channel: {e}")

# Test missing required property
try:
    bad_channel = mediatailor.Channel("BadChannel")
    bad_dict = bad_channel.to_dict()
    print(f"  Created Channel without required props (UNEXPECTED): {bad_dict}")
except ValueError as e:
    print(f"  Channel without required props raised ValueError: {e}")
except Exception as e:
    print(f"  Channel without required props raised: {e}")

print("\n" + "="*50)
print("Testing round-trip serialization...")

try:
    # Create a channel
    output = mediatailor.RequestOutputItem(
        ManifestName="manifest1", 
        SourceGroup="source1"
    )
    original = mediatailor.Channel(
        "RoundTripTest",
        ChannelName="TestChannel",
        PlaybackMode="LINEAR",
        Outputs=[output],
        Tier="BASIC"
    )
    
    # Serialize
    dict_repr = original.to_dict()
    print(f"  Serialized to dict with keys: {list(dict_repr.keys())}")
    
    # Try to reconstruct
    if "Properties" in dict_repr:
        reconstructed = mediatailor.Channel.from_dict("RoundTripTest", dict_repr["Properties"])
        reconstructed_dict = reconstructed.to_dict()
        
        if dict_repr == reconstructed_dict:
            print("  Round-trip successful: dictionaries match")
        else:
            print("  Round-trip FAILED: dictionaries don't match")
            print(f"    Original: {dict_repr}")
            print(f"    Reconstructed: {reconstructed_dict}")
    else:
        print(f"  No Properties in dict: {dict_repr}")
        
except Exception as e:
    print(f"  Round-trip test failed: {e}")
    import traceback
    traceback.print_exc()