"""Test bugs with normal object creation (not using validation=False)"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.controltower import EnabledBaseline, LandingZone

print("Testing bugs with normal object creation:")
print("=" * 50)

print("\nBug 1: Empty title validation")
print("-" * 30)
try:
    # Create with empty title - should fail per regex validation
    baseline = EnabledBaseline(
        "",  # Empty title
        BaselineIdentifier="id",
        BaselineVersion="1.0",
        TargetIdentifier="target"
    )
    print(f"✗ BUG CONFIRMED: Empty title '' was accepted")
    print(f"  Object created successfully with title='{baseline.title}'")
except ValueError as e:
    print(f"✓ Empty title rejected: {e}")

print("\nBug 2: Required fields validation") 
print("-" * 30)
try:
    # Create without required fields (normal creation, no validation=False)
    baseline = EnabledBaseline("TestBaseline")
    print(f"✗ BUG: Object created without required fields")
    # Try to use it
    result = baseline.to_dict()
    print(f"  to_dict succeeded: {result}")
except (ValueError, TypeError) as e:
    print(f"✓ Validation error raised: {e}")

print("\nBug 3: Title=None handling")
print("-" * 30)
try:
    # What about None title?
    baseline = EnabledBaseline(
        None,  # None title
        BaselineIdentifier="id",
        BaselineVersion="1.0",
        TargetIdentifier="target"
    )
    print(f"✗ None title was accepted: title={baseline.title}")
except (ValueError, TypeError) as e:
    print(f"✓ None title rejected: {e}")

print("\n" + "=" * 50)
print("SUMMARY:")
print("1. Empty string title ('') bypasses validation - CONFIRMED BUG")
print("2. Missing required fields ARE caught during normal usage")  
print("3. None title is accepted (may or may not be intentional)")