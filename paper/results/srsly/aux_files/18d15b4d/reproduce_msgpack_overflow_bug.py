#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')
import srsly

# Test msgpack with large integers
print("Testing msgpack with large integers:")

test_values = [
    2**63 - 1,      # Max signed 64-bit int
    2**63,          # Just over max signed 64-bit  
    2**64 - 1,      # Max unsigned 64-bit int
    2**64,          # Just over max unsigned 64-bit
    18446744073709551616,  # The value that Hypothesis found
]

for value in test_values:
    print(f"\nTesting value: {value}")
    print(f"  Bit length: {value.bit_length()} bits")
    
    try:
        # Test as single value
        serialized = srsly.msgpack_dumps(value)
        deserialized = srsly.msgpack_loads(serialized)
        print(f"  Single value: SUCCESS - round-trip works")
        assert deserialized == value
    except Exception as e:
        print(f"  Single value: FAILED - {e}")
    
    try:
        # Test as tuple
        tuple_data = (value,)
        serialized = srsly.msgpack_dumps(tuple_data)
        deserialized = srsly.msgpack_loads(serialized)
        print(f"  In tuple: SUCCESS - round-trip works")
        assert deserialized[0] == value
    except Exception as e:
        print(f"  In tuple: FAILED - {e}")
        
    try:
        # Test in list
        list_data = [value]
        serialized = srsly.msgpack_dumps(list_data)
        deserialized = srsly.msgpack_loads(serialized)
        print(f"  In list: SUCCESS - round-trip works")
        assert deserialized[0] == value
    except Exception as e:
        print(f"  In list: FAILED - {e}")