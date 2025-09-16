#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import troposphere.connectcampaigns as cc

print("Testing JSON standard compliance\n")

# Test Python's json module behavior
print("1. Testing Python's json.dumps() with special floats:")
test_values = {
    "nan": float('nan'),
    "inf": float('inf'),
    "neginf": float('-inf')
}

for name, value in test_values.items():
    try:
        result = json.dumps(value)
        print(f"  {name}: json.dumps() produced: {result}")
    except ValueError as e:
        print(f"  {name}: json.dumps() raised: {e}")

print("\n2. Testing with allow_nan=False (strict mode):")
for name, value in test_values.items():
    try:
        result = json.dumps(value, allow_nan=False)
        print(f"  {name}: Produced: {result}")
    except ValueError as e:
        print(f"  {name}: Correctly raised: {e}")

print("\n3. Testing troposphere's JSON generation:")
config = cc.AgentlessDialerConfig(DialingCapacity=float('nan'))
json_str = config.to_json()

# Check what's actually in the string
print(f"  Raw JSON output: {repr(json_str[:50])}")

# Try to validate it as proper JSON
print("\n4. Testing if CloudFormation would accept this:")
print("  According to JSON RFC 7159, NaN and Infinity are NOT valid JSON values.")
print("  CloudFormation requires valid JSON or YAML.")

# Write to file and try to load with strict parser
with open('test_output.json', 'w') as f:
    f.write(json_str)

print("\n5. Testing with external JSON validation:")
import subprocess
result = subprocess.run(['python3', '-m', 'json.tool', 'test_output.json'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("  Python's json.tool accepted it")
else:
    print(f"  Python's json.tool rejected it: {result.stderr}")

# Test round-trip
print("\n6. Testing round-trip with from_dict:")
d = config.to_dict()
print(f"  to_dict() result: {d}")

try:
    # Try to reconstruct
    reconstructed = cc.AgentlessDialerConfig._from_dict(**d)
    print(f"  Reconstructed successfully")
    print(f"  Reconstructed value: {reconstructed.properties.get('DialingCapacity')}")
    print(f"  Is NaN: {float('nan') != float('nan')}")  # NaN != NaN is always True
except Exception as e:
    print(f"  Reconstruction failed: {e}")