"""Minimal reproduction of deferred validation bug in troposphere.scheduler"""

from troposphere.scheduler import FlexibleTimeWindow, EventBridgeParameters

# BUG: Objects can be created without required fields
# No error is raised at creation time
ftw = FlexibleTimeWindow()  # Missing required 'Mode' field
ebp = EventBridgeParameters(DetailType="test")  # Missing required 'Source' field

print("Objects created successfully (no validation):")
print(f"  FlexibleTimeWindow: {ftw}")
print(f"  EventBridgeParameters: {ebp}")

# The error only appears when trying to serialize
print("\nAttempting to serialize FlexibleTimeWindow...")
try:
    ftw.to_dict()
    print("  SUCCESS (unexpected)")
except ValueError as e:
    print(f"  ERROR: {e}")

print("\nAttempting to serialize EventBridgeParameters...")
try:
    ebp.to_dict()
    print("  SUCCESS (unexpected)")
except ValueError as e:
    print(f"  ERROR: {e}")