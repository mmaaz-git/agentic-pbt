#!/usr/bin/env python3
"""Isolated test for the CopyFrom issue."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import coremltools.proto.DataStructures_pb2 as DS

safe_strings = st.text(min_size=0, max_size=1000)
safe_int64s = st.integers(min_value=-2**63+1, max_value=2**63-1)

@given(st.dictionaries(safe_strings, safe_int64s, min_size=0, max_size=50))
@settings(max_examples=500)
def test_copy_from_string_int64_map(mapping):
    """Test that CopyFrom creates an exact copy of StringToInt64Map."""
    msg1 = DS.StringToInt64Map()
    for k, v in mapping.items():
        msg1.map[k] = v
    
    msg2 = DS.StringToInt64Map()
    msg2.CopyFrom(msg1)
    
    # First check: maps should be equal
    assert dict(msg2.map) == mapping, f"Maps not equal: {dict(msg2.map)} vs {mapping}"
    
    # Second check: serializations should be equal
    ser1 = msg1.SerializeToString()
    ser2 = msg2.SerializeToString()
    
    if ser1 != ser2:
        print(f"\nFailing case found!")
        print(f"Mapping: {mapping}")
        print(f"msg1 map after setting: {dict(msg1.map)}")
        print(f"msg2 map after CopyFrom: {dict(msg2.map)}")
        print(f"Serialization lengths: {len(ser1)} vs {len(ser2)}")
        
        # Show hex diff
        print(f"ser1 hex: {ser1.hex()}")
        print(f"ser2 hex: {ser2.hex()}")
        
        # Find first difference
        for i, (b1, b2) in enumerate(zip(ser1, ser2)):
            if b1 != b2:
                print(f"First difference at byte {i}: 0x{b1:02x} vs 0x{b2:02x}")
                break
    
    assert ser1 == ser2, f"Serializations differ for mapping {mapping}"

if __name__ == "__main__":
    test_copy_from_string_int64_map()
    print("Test passed!")