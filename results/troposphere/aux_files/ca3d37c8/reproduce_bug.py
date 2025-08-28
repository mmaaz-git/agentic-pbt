#!/usr/bin/env python3
"""Minimal reproduction of the bug in validate_volume_configuration."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.opsworks import validate_volume_configuration


class MockVolumeConfig:
    def __init__(self, volume_type=None, iops=None):
        self.properties = {}
        if volume_type is not None:
            self.properties["VolumeType"] = volume_type
        if iops is not None:
            self.properties["Iops"] = iops


# Test case that fails
config = MockVolumeConfig(volume_type=None, iops=100)

try:
    validate_volume_configuration(config)
    print("No error raised - validation passed")
except ValueError as e:
    print(f"Error raised: {e}")
    print("\nThis is a bug because:")
    print("- VolumeType is not specified (None)")
    print("- The function assumes that when VolumeType != 'io1', it includes the case when VolumeType is None")
    print("- This causes it to reject Iops even when VolumeType is not set at all")
    print("\nThe logic should check if VolumeType is explicitly set to a non-io1 value before rejecting Iops")