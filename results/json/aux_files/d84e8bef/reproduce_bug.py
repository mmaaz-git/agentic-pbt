import json
import json.encoder

# Test the bug with infinity as a dict key
d = {float('inf'): 'value'}

encoder = json.encoder.JSONEncoder(skipkeys=False)
encoded = encoder.encode(d)
print(f"Encoded: {encoded}")

decoded = json.loads(encoded)
print(f"Decoded: {decoded}")

# What we expect vs what we get
print(f"\nOriginal key: {list(d.keys())[0]}")
print(f"Original key as string: '{float('inf')}'")
print(f"Decoded keys: {list(decoded.keys())}")

# The issue: float('inf') becomes 'Infinity' in JSON, 
# but str(float('inf')) is 'inf' in Python
print(f"\nstr(float('inf')) = '{str(float('inf'))}'")
print(f"JSON representation = 'Infinity'")

# Same issue with -inf
d2 = {float('-inf'): 'value'}
encoded2 = encoder.encode(d2)
decoded2 = json.loads(encoded2)
print(f"\nFor -inf:")
print(f"Original key: {list(d2.keys())[0]}")
print(f"Encoded: {encoded2}")
print(f"Decoded: {decoded2}")
print(f"str(float('-inf')) = '{str(float('-inf'))}'")

# And with NaN
d3 = {float('nan'): 'value'}
encoder_nan = json.encoder.JSONEncoder(skipkeys=False, allow_nan=True)
encoded3 = encoder_nan.encode(d3)
decoded3 = json.loads(encoded3)
print(f"\nFor NaN:")
print(f"Original key: {list(d3.keys())[0]}")
print(f"Encoded: {encoded3}")
print(f"Decoded: {decoded3}")
print(f"str(float('nan')) = '{str(float('nan'))}'")

# This creates an inconsistency in round-tripping
print("\n=== Round-trip inconsistency ===")
original = {float('inf'): 'a', float('-inf'): 'b', float('nan'): 'c'}
encoder_rt = json.encoder.JSONEncoder(allow_nan=True)
encoded_rt = encoder_rt.encode(original)
decoded_rt = json.loads(encoded_rt)

print(f"Original keys: {list(original.keys())}")
print(f"Encoded: {encoded_rt}")
print(f"Decoded keys: {list(decoded_rt.keys())}")
print(f"Round-trip preserves keys? {list(original.keys()) == list(decoded_rt.keys())}")