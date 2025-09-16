#!/usr/bin/env python3
"""Minimal reproduction scripts for found bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.imagebuilder as ib
import math

# Bug 1: Integer validator crashes on float infinity
print("Testing Bug 1: Integer validator with infinity...")
try:
    ebs = ib.EbsInstanceBlockDeviceSpecification()
    ebs.VolumeSize = float('inf')
    print("ERROR: Should have raised an error but didn't")
except OverflowError as e:
    print(f"BUG CONFIRMED: OverflowError when setting VolumeSize to infinity: {e}")
except Exception as e:
    print(f"Different error: {e}")

print()

# Bug 2: Integer validator crashes on NaN
print("Testing Bug 2: Integer validator with NaN...")
try:
    ebs = ib.EbsInstanceBlockDeviceSpecification()
    ebs.Iops = float('nan')
    print("ERROR: Should have raised an error but didn't")
except ValueError as e:
    print(f"BUG CONFIRMED: ValueError when setting Iops to NaN: {e}")
except Exception as e:
    print(f"Different error: {e}")

print()

# Bug 3: validation=False doesn't disable validation
print("Testing Bug 3: validation=False parameter...")
try:
    # This should not validate the platform value
    component = ib.Component(
        "TestComponent",
        Name="Test",
        Platform="InvalidPlatform",  # Not Linux or Windows
        Version="1.0",
        validation=False
    )
    print("Component created successfully with invalid platform and validation=False")
    # Try to serialize
    comp_dict = component.to_dict(validation=False)
    print("to_dict(validation=False) succeeded")
except ValueError as e:
    print(f"BUG CONFIRMED: validation=False doesn't work: {e}")
except Exception as e:
    print(f"Different error: {e}")

print()

# Bug 4: Very large integers
print("Testing Bug 4: Very large integers...")
try:
    ebs = ib.EbsInstanceBlockDeviceSpecification()
    ebs.VolumeSize = 2**63  # Extremely large but valid integer
    print(f"Successfully set VolumeSize to {ebs.VolumeSize}")
except Exception as e:
    print(f"Error with large integer: {e}")

print()

# Bug 5: Negative integers for unsigned properties
print("Testing Bug 5: Negative integers...")
try:
    ebs = ib.EbsInstanceBlockDeviceSpecification()
    ebs.VolumeSize = -100  # Negative volume size doesn't make sense
    print(f"BUG CONFIRMED: Accepted negative VolumeSize: {ebs.VolumeSize}")
except Exception as e:
    print(f"Correctly rejected negative value: {e}")