#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.arczonalshift import (
    ZonalAutoshiftConfiguration,
    PracticeRunConfiguration,
    ControlCondition
)

# Test 1: None for optional property in ZonalAutoshiftConfiguration
print("Test 1: None for optional PracticeRunConfiguration property")
try:
    config = ZonalAutoshiftConfiguration(
        "TestConfig",
        ResourceIdentifier="test-resource",
        PracticeRunConfiguration=None  # This is optional (False in props)
    )
    print("✓ Success - None accepted")
except TypeError as e:
    print(f"✗ Failed - {e}")

# Test 2: None for optional string property
print("\nTest 2: None for optional ZonalAutoshiftStatus property")
try:
    config = ZonalAutoshiftConfiguration(
        "TestConfig",
        ResourceIdentifier="test-resource",
        ZonalAutoshiftStatus=None  # This is optional (False in props)
    )
    print("✓ Success - None accepted")
except TypeError as e:
    print(f"✗ Failed - {e}")

# Test 3: Omitting optional properties (should work)
print("\nTest 3: Omitting optional properties entirely")
try:
    config = ZonalAutoshiftConfiguration(
        "TestConfig",
        ResourceIdentifier="test-resource"
        # Not providing optional properties
    )
    result = config.to_dict(validation=True)
    print(f"✓ Success - Optional properties can be omitted")
    print(f"  Properties in result: {list(result['Properties'].keys())}")
except Exception as e:
    print(f"✗ Failed - {e}")

# Test 4: None for optional list properties in PracticeRunConfiguration
print("\nTest 4: None for optional list properties")
try:
    cc = ControlCondition(AlarmIdentifier="test", Type="test")
    config = PracticeRunConfiguration(
        BlockedDates=None,  # Optional list property
        OutcomeAlarms=[cc]  # Required
    )
    print("✓ Success - None accepted for optional list")
except TypeError as e:
    print(f"✗ Failed - {e}")

# Test 5: Check what happens if we just don't set the property
print("\nTest 5: Properties behavior comparison")
config1 = ZonalAutoshiftConfiguration(
    "TestConfig",
    ResourceIdentifier="test-resource"
)
print(f"Without setting property: 'PracticeRunConfiguration' in config1.properties = {
    'PracticeRunConfiguration' in config1.properties}")

# Now try to explicitly delete it
try:
    del config1.PracticeRunConfiguration
    print("Property deletion successful")
except:
    print("Property cannot be deleted")