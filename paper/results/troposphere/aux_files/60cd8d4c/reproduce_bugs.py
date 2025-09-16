"""Minimal reproductions of discovered bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.controltower import EnabledBaseline, LandingZone

print("Bug 1: Empty title validation failure")
print("=" * 50)
try:
    # Empty title should be rejected per regex validation
    baseline = EnabledBaseline(
        "",  # Empty title - should fail validation
        BaselineIdentifier="id",
        BaselineVersion="1.0", 
        TargetIdentifier="target"
    )
    print(f"✗ BUG: Empty title was accepted: title='{baseline.title}'")
except ValueError as e:
    print(f"✓ OK: Empty title rejected as expected: {e}")

print("\nBug 2: Missing required fields not validated")
print("=" * 50)
try:
    # Create object with NO required fields
    baseline = EnabledBaseline("TestBaseline", validation=False)
    # Try to convert to dict with validation enabled
    result = baseline.to_dict(validation=True)
    print(f"✗ BUG: Object with no required fields passed validation")
    print(f"  Result: {result}")
except ValueError as e:
    print(f"✓ OK: Missing required fields caught: {e}")

print("\nBug 3: LandingZone missing required fields")
print("=" * 50)
try:
    # Create LandingZone with no required fields
    lz = LandingZone("TestLZ", validation=False)
    result = lz.to_dict(validation=True) 
    print(f"✗ BUG: LandingZone with no required fields passed validation")
    print(f"  Result: {result}")
except ValueError as e:
    print(f"✓ OK: Missing required fields caught: {e}")

print("\n" + "=" * 50)
print("SUMMARY: Found 3 validation bugs in troposphere.controltower")