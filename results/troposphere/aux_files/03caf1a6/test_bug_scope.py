#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.fis as fis

print("Testing if None handling bug affects other classes...")
print("="*60)

# Test other classes with optional properties
test_cases = [
    ("S3Configuration", fis.S3Configuration, {"BucketName": "test", "Prefix": None}),
    ("ExperimentReportS3Configuration", fis.ExperimentReportS3Configuration, {"BucketName": "test", "Prefix": None}),
    ("ExperimentTemplateAction", fis.ExperimentTemplateAction, {"ActionId": "test", "Description": None}),
    ("ExperimentTemplateStopCondition", fis.ExperimentTemplateStopCondition, {"Source": "test", "Value": None}),
    ("CloudWatchLogsConfiguration", fis.CloudWatchLogsConfiguration, {"LogGroupArn": "test"}),
]

for name, cls, props in test_cases:
    try:
        obj = cls(**props)
        obj.to_dict()
        print(f"✓ {name}: Handles None correctly")
    except (TypeError, ValueError) as e:
        if "NoneType" in str(e):
            print(f"✗ {name}: Cannot handle None for optional properties")
        else:
            print(f"? {name}: Different error: {e}")

print("\nConclusion: This appears to be a systematic issue with None handling for optional properties")