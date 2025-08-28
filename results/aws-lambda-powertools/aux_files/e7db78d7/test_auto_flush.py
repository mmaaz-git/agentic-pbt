#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from unittest.mock import patch, MagicMock, call
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.constants import MAX_METRICS
import json

print(f"Testing auto-flush at MAX_METRICS={MAX_METRICS}")
print("=" * 70)

# Test 1: Check if flush happens at 100 metrics
print("\nTest 1: Adding 100 different metrics")
print("-" * 70)

provider = AmazonCloudWatchEMFProvider(namespace="TestNamespace")
mock_print = MagicMock()

with patch('builtins.print', mock_print):
    # Add 100 metrics
    for i in range(100):
        provider.add_metric(name=f"Metric_{i}", unit=MetricUnit.Count, value=i)
    
    print(f"After adding 100 metrics:")
    print(f"  - Print was called (flush happened): {mock_print.called}")
    print(f"  - Number of calls: {mock_print.call_count}")
    print(f"  - Current metric_set size: {len(provider.metric_set)}")
    
    if mock_print.called:
        # Check the actual call
        args_list = mock_print.call_args_list
        for idx, call_args in enumerate(args_list):
            if call_args[0]:  # If there are positional arguments
                arg = call_args[0][0]
                if isinstance(arg, str) and arg.startswith('{'):
                    try:
                        data = json.loads(arg)
                        if "_aws" in data:
                            metrics_count = len(data["_aws"]["CloudWatchMetrics"][0]["Metrics"])
                            print(f"  - Flush #{idx+1}: {metrics_count} metrics")
                    except:
                        pass

# Test 2: Check if flush happens when single metric has 100 values
print("\nTest 2: Adding 100 values to a single metric")
print("-" * 70)

provider2 = AmazonCloudWatchEMFProvider(namespace="TestNamespace")
mock_print2 = MagicMock()

with patch('builtins.print', mock_print2):
    # Add same metric 100 times
    for i in range(100):
        provider2.add_metric(name="SingleMetric", unit=MetricUnit.Count, value=i)
    
    print(f"After adding 100 values to one metric:")
    print(f"  - Print was called (flush happened): {mock_print2.called}")
    print(f"  - Number of calls: {mock_print2.call_count}")
    print(f"  - Current metric_set size: {len(provider2.metric_set)}")
    
    if mock_print2.called:
        # Check the actual call
        args_list = mock_print2.call_args_list
        for idx, call_args in enumerate(args_list):
            if call_args[0]:  # If there are positional arguments
                arg = call_args[0][0]
                if isinstance(arg, str) and arg.startswith('{'):
                    try:
                        data = json.loads(arg)
                        if "_aws" in data:
                            # Check the metric values
                            if "SingleMetric" in data:
                                values_count = len(data["SingleMetric"])
                                print(f"  - Flush #{idx+1}: SingleMetric has {values_count} values")
                    except:
                        pass

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)

if mock_print.called and mock_print.call_count == 1:
    print("✓ Flush happens when reaching 100 different metrics")
else:
    print("✗ Unexpected behavior for 100 different metrics")

if mock_print2.called and mock_print2.call_count == 1:
    print("✓ Flush happens when a single metric reaches 100 values")
else:
    print("✗ Unexpected behavior for 100 values in single metric")