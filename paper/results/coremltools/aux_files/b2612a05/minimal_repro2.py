#!/usr/bin/env python3
"""Minimal reproduction of the CopyFrom serialization order bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import coremltools.proto.DataStructures_pb2 as DS

# This specific case was failing in the test
test_cases = [
    {'2': 0, '4': 0, '00000': 0, '00000000000000': 0},
    {'000': 0, '001': 0, '0000': 0},
    {'å\U0008814c': 0, 'Å®£+': 0, '00100': 0, '000': 0},
]

for i, mapping in enumerate(test_cases):
    print(f"\nTest case {i+1}: {mapping}")
    print("="*60)
    
    msg1 = DS.StringToInt64Map()
    for k, v in mapping.items():
        msg1.map[k] = v
    
    msg2 = DS.StringToInt64Map()
    msg2.CopyFrom(msg1)
    
    # The maps are equal
    print(f"Maps equal: {dict(msg1.map) == dict(msg2.map)}")
    print(f"msg1 map: {dict(msg1.map)}")
    print(f"msg2 map: {dict(msg2.map)}")
    
    # But serializations might differ
    ser1 = msg1.SerializeToString()
    ser2 = msg2.SerializeToString()
    
    if ser1 != ser2:
        print(f"SERIALIZATIONS DIFFER!")
        print(f"  msg1 hex: {ser1.hex()}")
        print(f"  msg2 hex: {ser2.hex()}")
        
        # Find first difference
        for j, (b1, b2) in enumerate(zip(ser1, ser2)):
            if b1 != b2:
                print(f"  First diff at byte {j}: 0x{b1:02x} vs 0x{b2:02x}")
                break
    else:
        print(f"Serializations equal: True")