#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from unittest.mock import patch
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider
from aws_lambda_powertools.metrics import MetricUnit

# Create provider with namespace
provider = AmazonCloudWatchEMFProvider(namespace="TestNamespace")

# Check the MAX_METRICS constant
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.constants import MAX_METRICS
print(f"MAX_METRICS constant: {MAX_METRICS}")

# Track if print was called
print_called = False
original_print = print

def mock_print(*args, **kwargs):
    global print_called
    print_called = True
    original_print("FLUSH CALLED:", *args, **kwargs)

# Patch print to track calls
with patch('builtins.print', side_effect=mock_print):
    # Add metrics up to MAX_METRICS
    for i in range(MAX_METRICS):
        metric_name = f"Metric_{i}"
        provider.add_metric(name=metric_name, unit=MetricUnit.Count, value=i)
        print(f"Added metric {i+1}/{MAX_METRICS}: {metric_name}")
        print(f"Current metric_set size: {len(provider.metric_set)}")
        
        # Check if the 100th metric triggered a flush
        if i == MAX_METRICS - 1:
            print(f"After adding metric {i+1}, print_called: {print_called}")
            print(f"Metric set after 100th metric: {list(provider.metric_set.keys())}")

print(f"\nFinal state:")
print(f"Print was called (flush happened): {print_called}")
print(f"Final metric_set size: {len(provider.metric_set)}")
print(f"Final metrics: {list(provider.metric_set.keys())}")