import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.appintegrations import (
    ExternalUrlConfig, ApplicationSourceConfig, Application,
    DataIntegration, ScheduleConfig, EventIntegration, EventFilter,
    FileConfiguration
)

print("Testing bug 1: ExternalUrlConfig with empty list for ApprovedOrigins")
try:
    config = ExternalUrlConfig(
        AccessUrl="https://example.com",
        ApprovedOrigins=[]  # Empty list should be valid
    )
    print("Success: Empty list accepted")
except TypeError as e:
    print(f"BUG FOUND: {e}")

print("\nTesting bug 2: ExternalUrlConfig with None for optional ApprovedOrigins")
try:
    config = ExternalUrlConfig(
        AccessUrl="https://example.com",
        ApprovedOrigins=None  # None should be valid for optional field
    )
    print("Success: None accepted for optional field")
except TypeError as e:
    print(f"BUG FOUND: {e}")

print("\nTesting bug 3: DataIntegration with None for optional Description")
try:
    di = DataIntegration(
        title="TestDI",
        Name="test",
        KmsKey="test-key",
        SourceURI="s3://bucket/path",
        Description=None  # None should be valid for optional field
    )
    print("Success: None accepted for optional Description")
except TypeError as e:
    print(f"BUG FOUND: {e}")

print("\nTesting bug 4: ScheduleConfig with None for optional fields")
try:
    sc = ScheduleConfig(
        ScheduleExpression="rate(1 hour)",
        FirstExecutionFrom=None,  # None should be valid for optional field
        Object=None  # None should be valid for optional field
    )
    print("Success: None accepted for optional fields")
except TypeError as e:
    print(f"BUG FOUND: {e}")

print("\nTesting bug 5: EventIntegration with None for optional Description")
try:
    ef = EventFilter(Source="aws.ec2")
    ei = EventIntegration(
        title="TestEvent",
        Name="test",
        EventBridgeBus="default",
        EventFilter=ef,
        Description=None  # None should be valid for optional field
    )
    print("Success: None accepted for optional Description")
except TypeError as e:
    print(f"BUG FOUND: {e}")

print("\nTesting bug 6: FileConfiguration with None for optional Filters")
try:
    fc = FileConfiguration(
        Folders=["/path/to/folder"],
        Filters=None  # None should be valid for optional field
    )
    print("Success: None accepted for optional Filters")
except TypeError as e:
    print(f"BUG FOUND: {e}")

print("\nChecking documentation/expectations...")
print("According to the props definitions:")
print("- ExternalUrlConfig.ApprovedOrigins: ([str], False) - False means optional")
print("- DataIntegration.Description: (str, False) - False means optional")
print("- ScheduleConfig.FirstExecutionFrom: (str, False) - False means optional")
print("- EventIntegration.Description: (str, False) - False means optional")
print("- FileConfiguration.Filters: (dict, False) - False means optional")
print("\nConclusion: The library incorrectly rejects None for optional fields.")