#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.connectcampaigns as cc
import math
import json

# Test NaN handling
print("Testing NaN handling in troposphere.connectcampaigns")

# Create config with NaN
config = cc.AgentlessDialerConfig(DialingCapacity=float('nan'))
print(f"Created config with NaN: {config.properties}")

# Try to serialize to dict
try:
    d = config.to_dict()
    print(f"to_dict() result: {d}")
    
    # Try to serialize to JSON
    json_str = config.to_json()
    print(f"to_json() result: {json_str}")
    
    # Try to parse it back
    parsed = json.loads(json_str)
    print(f"Parsed JSON: {parsed}")
    
except Exception as e:
    print(f"Error during serialization: {e}")

# Test infinity
print("\nTesting infinity handling")
config_inf = cc.AgentlessDialerConfig(DialingCapacity=float('inf'))
print(f"Created config with inf: {config_inf.properties}")

try:
    d_inf = config_inf.to_dict()
    print(f"to_dict() with inf: {d_inf}")
    
    json_str_inf = config_inf.to_json()
    print(f"to_json() with inf: {json_str_inf}")
    
    parsed_inf = json.loads(json_str_inf)
    print(f"Parsed JSON with inf: {parsed_inf}")
    
except Exception as e:
    print(f"Error with infinity: {e}")

# Test -infinity
print("\nTesting -infinity handling")
config_neginf = cc.AgentlessDialerConfig(DialingCapacity=float('-inf'))

try:
    json_str_neginf = config_neginf.to_json()
    print(f"to_json() with -inf: {json_str_neginf}")
    parsed_neginf = json.loads(json_str_neginf)
    
except Exception as e:
    print(f"Error with -infinity: {e}")