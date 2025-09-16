#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from unittest.mock import patch, MagicMock
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.constants import MAX_METRICS
import json

# Create provider with namespace
provider = AmazonCloudWatchEMFProvider(namespace="TestNamespace")

# Create a mock for print
mock_print = MagicMock()

print(f"Testing with MAX_METRICS={MAX_METRICS}")
print("-" * 60)

with patch('builtins.print', mock_print):
    # Add exactly MAX_METRICS metrics
    for i in range(MAX_METRICS):
        provider.add_metric(name=f"Metric_{i}", unit=MetricUnit.Count, value=i)
    
    print(f"After adding {MAX_METRICS} metrics:")
    print(f"  - Print called: {mock_print.called}")
    print(f"  - Number of print calls: {mock_print.call_count}")
    print(f"  - Current metric_set size: {len(provider.metric_set)}")
    
    if mock_print.called:
        # Get the JSON that was printed
        call_args = mock_print.call_args[0][0]
        data = json.loads(call_args)
        metrics_in_flush = len(data["_aws"]["CloudWatchMetrics"][0]["Metrics"])
        print(f"  - Metrics in flush: {metrics_in_flush}")
    
    # Reset the mock
    mock_print.reset_mock()
    
    # Now add one more metric
    print(f"\nAdding metric #{MAX_METRICS + 1}...")
    provider.add_metric(name=f"Metric_{MAX_METRICS}", unit=MetricUnit.Count, value=MAX_METRICS)
    
    print(f"After adding {MAX_METRICS + 1} metrics:")
    print(f"  - Print called: {mock_print.called}")
    print(f"  - Number of print calls: {mock_print.call_count}")
    print(f"  - Current metric_set size: {len(provider.metric_set)}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)

# Now let's trace through what actually happens
print("\nDetailed trace of what happens at the boundary:")
print("-" * 60)

# Reset and do a detailed trace
provider2 = AmazonCloudWatchEMFProvider(namespace="TestNamespace")

for i in range(98, 102):
    if i < 102:
        print(f"\nBefore adding metric #{i+1}:")
        print(f"  metric_set size: {len(provider2.metric_set)}")
        
        with patch('builtins.print') as mock:
            provider2.add_metric(name=f"M{i}", unit=MetricUnit.Count, value=i)
            print(f"After adding metric #{i+1}:")
            print(f"  metric_set size: {len(provider2.metric_set)}")
            print(f"  Flush happened: {mock.called}")
            
            if mock.called and i == 99:  # The 100th metric (0-indexed)
                # Verify what was flushed
                call_args = mock.call_args[0][0]
                data = json.loads(call_args)
                metrics_count = len(data["_aws"]["CloudWatchMetrics"][0]["Metrics"])
                print(f"  Metrics in flush: {metrics_count}")
                print(f"  ✓ Flush happened at exactly {MAX_METRICS} metrics")