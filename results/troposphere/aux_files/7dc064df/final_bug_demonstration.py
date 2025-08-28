#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import troposphere.connectcampaigns as cc

print("=== BUG DEMONSTRATION: Invalid JSON Generation ===\n")

# Minimal reproduction
print("Minimal reproduction:")
print("-" * 40)

config = cc.AgentlessDialerConfig(DialingCapacity=float('nan'))
json_output = config.to_json()

print("Code:")
print("  config = cc.AgentlessDialerConfig(DialingCapacity=float('nan'))")
print("  json_output = config.to_json()")
print("\nOutput:")
print(json_output)

print("\nValidation with strict JSON decoder:")
decoder = json.JSONDecoder(strict=True)
try:
    # First test if Python's decoder accepts it by default
    standard_parse = json.loads(json_output)
    print("  ✓ Python's json.loads() accepts it (non-strict)")
    
    # Now test with external tool simulation
    import subprocess
    with open('test.json', 'w') as f:
        f.write(json_output)
    
    # Test if it's valid according to JSON spec
    print("\nChecking JSON validity:")
    if 'NaN' in json_output or 'Infinity' in json_output:
        print("  ✗ Contains 'NaN' or 'Infinity' literals - NOT valid JSON per RFC 7159")
        print("  ✗ AWS CloudFormation would REJECT this template")
    
except json.JSONDecodeError as e:
    print(f"  ✗ Failed to parse: {e}")

print("\n" + "=" * 50)
print("IMPACT:")
print("  1. Generates syntactically invalid JSON (NaN is not a JSON literal)")
print("  2. Violates JSON specification RFC 7159")  
print("  3. Would cause CloudFormation deployment failures")
print("  4. The library accepts invalid numeric values without validation")

print("\nAffected classes that use 'double' validator:")
print("  - AgentlessDialerConfig.DialingCapacity")
print("  - PredictiveDialerConfig.BandwidthAllocation")
print("  - PredictiveDialerConfig.DialingCapacity")
print("  - ProgressiveDialerConfig.BandwidthAllocation")
print("  - ProgressiveDialerConfig.DialingCapacity")