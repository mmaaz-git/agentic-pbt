#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.mediaconvert as mc

print("Testing troposphere.mediaconvert properties...")

# Test 1: Required field validation
print("\n1. Testing required field validation...")
jt = mc.JobTemplate("TestTemplate")
try:
    jt.to_dict()
    print("  BUG FOUND: JobTemplate.to_dict() should fail without required SettingsJson")
except ValueError as e:
    if "SettingsJson" in str(e) and "required" in str(e):
        print("  ✓ Required field validation works correctly")
    else:
        print(f"  ? Unexpected error: {e}")

# Test 2: Integer validation with string
print("\n2. Testing integer validation...")
jt2 = mc.JobTemplate("Test2", SettingsJson={})
try:
    jt2.Priority = "not_a_number"
    print("  BUG FOUND: Priority accepted string 'not_a_number' instead of integer")
except (ValueError, TypeError) as e:
    print("  ✓ Integer validation rejected non-integer")

# Test 3: Test with actual integer string
try:
    jt2.Priority = "42"
    if jt2.Priority == "42":
        print("  ✓ Integer validator accepts string representation of integer")
    else:
        print(f"  ? Priority became {jt2.Priority}")
except (ValueError, TypeError) as e:
    print(f"  ? Unexpected rejection of '42': {e}")

# Test 4: Test serialization round-trip
print("\n3. Testing serialization round-trip...")
original = mc.JobTemplate("RoundTrip", 
                          SettingsJson={"key": "value"},
                          Priority=5,
                          Category="Test")

serialized = original.to_dict()
properties = serialized.get("Properties", {})
restored = mc.JobTemplate.from_dict("RoundTrip", properties)

if original.to_dict() == restored.to_dict():
    print("  ✓ Round-trip serialization works correctly")
else:
    print("  BUG FOUND: Round-trip serialization failed")
    print(f"    Original: {original.to_dict()}")
    print(f"    Restored: {restored.to_dict()}")

# Test 5: Test with no validation
print("\n4. Testing validation=False mode...")
jt_no_val = mc.JobTemplate("NoValidation", validation=False)
try:
    result = jt_no_val.to_dict(validation=False)
    print(f"  ✓ Can create and serialize without required fields when validation=False")
except ValueError as e:
    print(f"  ? Still got error with validation=False: {e}")

# Test 6: Test HopDestinations list property
print("\n5. Testing list property handling...")
hop1 = mc.HopDestination(Priority=1, Queue="queue1", WaitMinutes=5)
hop2 = mc.HopDestination(Priority=2, Queue="queue2", WaitMinutes=10)

jt_with_hops = mc.JobTemplate("WithHops",
                              SettingsJson={},
                              HopDestinations=[hop1, hop2])

result = jt_with_hops.to_dict()
props = result.get("Properties", {})

if "HopDestinations" in props and len(props["HopDestinations"]) == 2:
    print("  ✓ List properties work correctly")
else:
    print("  BUG FOUND: HopDestinations not properly serialized")
    print(f"    Result: {result}")

print("\nTests completed!")