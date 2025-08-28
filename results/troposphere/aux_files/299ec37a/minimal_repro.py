#!/usr/bin/env python3
"""Minimal reproduction of the None handling bug in troposphere."""
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.iotfleetwise as iotfleetwise

print("Demonstrating the bug:")
print("="*60)

# This works - omitting optional Description
fleet1 = iotfleetwise.Fleet(
    title="Fleet1",
    Id="fleet-1",
    SignalCatalogArn="arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test"
)
print("✓ Created Fleet without Description field")

# This fails - explicitly setting optional Description to None
try:
    fleet2 = iotfleetwise.Fleet(
        title="Fleet2",
        Id="fleet-2",
        SignalCatalogArn="arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test",
        Description=None  # Explicitly set to None
    )
    print("✓ Created Fleet with Description=None")
except TypeError as e:
    print(f"✗ Failed to create Fleet with Description=None")
    print(f"  Error: {e}")

print("\nWhy this is a bug:")
print("-" * 40)
print("1. Description is marked as optional (False) in Fleet.props")
print("2. Optional properties should accept None as a valid value")
print("3. There's inconsistent behavior: omitting vs explicitly setting to None")
print("4. This breaks common patterns like dict unpacking with None values")