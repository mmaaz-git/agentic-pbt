import json
import json.encoder
from hypothesis import given, strategies as st, settings
import math

@given(st.dictionaries(
    st.floats(),
    st.text(),
    min_size=1,
    max_size=5
))
@settings(max_examples=1000)
def test_float_key_collision(d):
    """Test for key collision with special float values"""
    encoder = json.encoder.JSONEncoder(allow_nan=True)
    
    # Check if dictionary contains special floats as keys
    has_inf = any(math.isinf(k) and k > 0 for k in d.keys() if isinstance(k, float))
    has_neg_inf = any(math.isinf(k) and k < 0 for k in d.keys() if isinstance(k, float))
    has_nan = any(math.isnan(k) for k in d.keys() if isinstance(k, float))
    
    # Encode and decode
    encoded = encoder.encode(d)
    decoded = json.loads(encoded)
    
    # Check for key collisions
    original_keys_str = set()
    for k in d.keys():
        if isinstance(k, float):
            if math.isnan(k):
                original_keys_str.add('NaN')
            elif math.isinf(k) and k > 0:
                original_keys_str.add('Infinity')
            elif math.isinf(k) and k < 0:
                original_keys_str.add('-Infinity')
            else:
                original_keys_str.add(str(k))
        else:
            original_keys_str.add(str(k))
    
    # The bug: if we have both float('inf') and the string 'Infinity' as keys,
    # they collide in JSON
    if has_inf and 'Infinity' in str(d.keys()):
        # This should preserve both keys but doesn't
        assert len(decoded) < len(d), f"Key collision not detected: {d}"
    
    if has_neg_inf and '-Infinity' in str(d.keys()):
        assert len(decoded) < len(d), f"Key collision not detected: {d}"
        
    if has_nan and 'NaN' in str(d.keys()):
        assert len(decoded) < len(d), f"Key collision not detected: {d}"


if __name__ == "__main__":
    # Direct test case
    test_cases = [
        {'Infinity': 'a', float('inf'): 'b'},
        {'-Infinity': 'a', float('-inf'): 'b'},
        {'NaN': 'a', float('nan'): 'b'},
    ]
    
    for test_dict in test_cases:
        encoder = json.encoder.JSONEncoder(allow_nan=True)
        encoded = encoder.encode(test_dict)
        decoded = json.loads(encoded)
        
        print(f"\nOriginal: {test_dict}")
        print(f"Original keys: {list(test_dict.keys())} (len={len(test_dict)})")
        print(f"Encoded: {encoded}")
        print(f"Decoded: {decoded}")
        print(f"Decoded keys: {list(decoded.keys())} (len={len(decoded)})")
        print(f"BUG: Lost {len(test_dict) - len(decoded)} key(s)!")
        
        # The bug causes silent data loss
        assert len(decoded) < len(test_dict), "Key collision causes data loss"