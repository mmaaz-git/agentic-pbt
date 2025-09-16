"""Reproduce Bug 2: KeyValueClass accepts empty string as property name"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import emr as emr_validators

# Test: Empty string as property name
print("Test 1: Empty string as property name")
try:
    kv = emr_validators.KeyValueClass(**{"": "value"})
    print(f"BUG: KeyValueClass accepted empty string as property name")
    print(f"Properties: {kv.properties}")
except AttributeError as e:
    print(f"AttributeError (bug): {e}")
except (TypeError, ValueError) as e:
    print(f"Expected error: {e}")

# Test: Normal usage
print("\nTest 2: Normal usage with Key and Value")
try:
    kv = emr_validators.KeyValueClass(Key="mykey", Value="myvalue")
    print(f"SUCCESS: Created KeyValueClass with Key={kv.properties.get('Key')}, Value={kv.properties.get('Value')}")
except Exception as e:
    print(f"ERROR: {e}")

# Test: Using key and value parameters
print("\nTest 3: Using key and value parameters (backward compatibility)")
try:
    kv = emr_validators.KeyValueClass(key="mykey", value="myvalue")
    print(f"SUCCESS: Created KeyValueClass with Key={kv.properties.get('Key')}, Value={kv.properties.get('Value')}")
except Exception as e:
    print(f"ERROR: {e}")

# Test: Invalid property name
print("\nTest 4: Invalid property name (not Key or Value)")
try:
    kv = emr_validators.KeyValueClass(InvalidProp="value")
    print(f"BUG: KeyValueClass accepted invalid property name")
    print(f"Properties: {kv.properties}")
except AttributeError as e:
    print(f"Expected AttributeError: {e}")