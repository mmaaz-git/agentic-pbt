#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.opensearchservice import (
    WindowStartTime,
    NodeConfig,
    ZoneAwarenessConfig
)
from troposphere.validators.opensearchservice import validate_search_service_engine_version

print("=" * 60)
print("BUG 1: Engine version validator accepts invalid separators")
print("=" * 60)

# Bug 1: The regex accepts any character as separator, not just dots
invalid_versions = [
    "OpenSearch_1X2",      # X instead of .
    "Elasticsearch_3#4",   # # instead of .
    "OpenSearch_5A6",      # A instead of .
    "Elasticsearch_7!8",   # ! instead of .
]

for version in invalid_versions:
    try:
        result = validate_search_service_engine_version(version)
        print(f"✗ ACCEPTED (BUG): {version}")
    except ValueError:
        print(f"✓ REJECTED: {version}")

print("\n" + "=" * 60)
print("BUG 2: WindowStartTime accepts invalid hour/minute values")
print("=" * 60)

# Bug 2: WindowStartTime doesn't validate hour/minute ranges
invalid_times = [
    (25, 30),    # Hour > 23
    (12, 70),    # Minute > 59
    (-1, 30),    # Negative hour
    (12, -5),    # Negative minute
    (100, 200),  # Both out of range
]

for hours, minutes in invalid_times:
    try:
        window = WindowStartTime(Hours=hours, Minutes=minutes)
        print(f"✗ ACCEPTED (BUG): Hours={hours}, Minutes={minutes}")
    except (ValueError, TypeError) as e:
        print(f"✓ REJECTED: Hours={hours}, Minutes={minutes}")

print("\n" + "=" * 60)
print("BUG 3: NodeConfig accepts negative node counts")
print("=" * 60)

# Bug 3: NodeConfig doesn't validate that Count should be non-negative
negative_counts = [-1, -10, -100, -9999]

for count in negative_counts:
    try:
        node = NodeConfig(Count=count)
        print(f"✗ ACCEPTED (BUG): Count={count}")
    except (ValueError, TypeError) as e:
        print(f"✓ REJECTED: Count={count}")

print("\n" + "=" * 60)
print("BUG 4: ZoneAwarenessConfig accepts invalid AZ counts")
print("=" * 60)

# Bug 4: ZoneAwarenessConfig doesn't validate reasonable AZ count ranges
invalid_az_counts = [-1, -10, 0, 100, 1000, -9999]

for az_count in invalid_az_counts:
    try:
        config = ZoneAwarenessConfig(AvailabilityZoneCount=az_count)
        print(f"✗ ACCEPTED (BUG): AvailabilityZoneCount={az_count}")
    except (ValueError, TypeError) as e:
        print(f"✓ REJECTED: AvailabilityZoneCount={az_count}")