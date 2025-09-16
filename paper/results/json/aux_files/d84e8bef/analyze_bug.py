import json.encoder

# Looking at the code, in _iterencode_dict (line 361-372):
# When a float key is encountered, it uses _floatstr to convert it

# _floatstr is defined in iterencode (line 224-244)
# Let's simulate what happens:

def floatstr_behavior(o):
    """Simulating the floatstr function behavior"""
    INFINITY = float('inf')
    if o != o:  # NaN check
        return 'NaN'
    elif o == INFINITY:
        return 'Infinity'
    elif o == -INFINITY:
        return '-Infinity'
    else:
        return float.__repr__(o)

# Test the behavior
print("floatstr behavior:")
print(f"float('inf') -> '{floatstr_behavior(float('inf'))}'")
print(f"float('-inf') -> '{floatstr_behavior(float('-inf'))}'")
print(f"float('nan') -> '{floatstr_behavior(float('nan'))}'")
print(f"3.14 -> '{floatstr_behavior(3.14)}'")

print("\nPython str() behavior:")
print(f"str(float('inf')) -> '{str(float('inf'))}'")
print(f"str(float('-inf')) -> '{str(float('-inf'))}'")
print(f"str(float('nan')) -> '{str(float('nan'))}'")
print(f"str(3.14) -> '{str(3.14)}'")

print("\n=== The Problem ===")
print("JSON encoder converts special float keys using JSON names (Infinity, -Infinity, NaN)")
print("But Python's str() uses different names (inf, -inf, nan)")
print("This creates an inconsistency where the round-trip changes the keys!")

# More problematic: collision potential
print("\n=== Collision Example ===")
d = {'Infinity': 'string_key', float('inf'): 'float_key'}
print(f"Original dict: {d}")
try:
    encoded = json.encoder.JSONEncoder().encode(d)
    print(f"Encoded: {encoded}")
    decoded = json.loads(encoded)
    print(f"Decoded: {decoded}")
    print(f"Data loss! Original had {len(d)} keys, decoded has {len(decoded)} keys")
except Exception as e:
    print(f"Error: {e}")

# Even worse with skipkeys=True - silent data loss
print("\n=== Silent data loss with skipkeys=True ===")
d2 = {'Infinity': 'value1', float('inf'): 'value2'}
encoder = json.encoder.JSONEncoder(skipkeys=True)
encoded = encoder.encode(d2)
print(f"Original: {d2}")
print(f"Encoded: {encoded}")
decoded = json.loads(encoded)
print(f"Decoded: {decoded}")
print(f"Silent overwrite: value2 overwrote value1!")