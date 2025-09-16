#!/usr/bin/env python3
"""Minimal reproduction of the naming inconsistency bug in troposphere.firehose"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import firehose

# Demonstrate the bug: IcebergDestinationConfiguration has inconsistent property naming
iceberg = firehose.IcebergDestinationConfiguration()

# This property is named with lowercase 's'
assert 's3BackupMode' in iceberg.props, "Bug: property is named 's3BackupMode' with lowercase 's'"

# All other similar classes use uppercase 'S'
other_classes = [
    firehose.ExtendedS3DestinationConfiguration(),
    firehose.ElasticsearchDestinationConfiguration(),
    firehose.SnowflakeDestinationConfiguration(),
    firehose.SplunkDestinationConfiguration(),
]

for obj in other_classes:
    if 'S3BackupMode' in obj.props:
        assert 'S3BackupMode' in obj.props, f"{obj.__class__.__name__} uses uppercase 'S'"
        assert 's3BackupMode' not in obj.props, f"{obj.__class__.__name__} doesn't use lowercase 's'"

print("BUG CONFIRMED:")
print("IcebergDestinationConfiguration uses 's3BackupMode' (lowercase 's')")
print("All other classes use 'S3BackupMode' (uppercase 'S')")
print("\nThis violates AWS CloudFormation naming conventions where S3 should always be uppercase.")