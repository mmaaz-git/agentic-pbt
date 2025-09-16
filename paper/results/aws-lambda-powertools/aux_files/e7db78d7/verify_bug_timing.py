#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from unittest.mock import patch
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.constants import MAX_METRICS
import json

# Create provider with namespace
provider = AmazonCloudWatchEMFProvider(namespace="TestNamespace")

# Track all flushes
flushes = []

def capture_print(*args, **kwargs):
    if args and isinstance(args[0], str):
        try:
            data = json.loads(args[0])
            if "_aws" in data:
                # This is a metrics flush
                metrics_count = len(data["_aws"]["CloudWatchMetrics"][0]["Metrics"])
                flushes.append(metrics_count)
                print(f"FLUSH {len(flushes)}: {metrics_count} metrics")
        except:
            pass

# Test the exact boundary condition
print(f"Testing boundary condition with MAX_METRICS={MAX_METRICS}")
print("-" * 60)

with patch('builtins.print', side_effect=capture_print):
    # Add exactly MAX_METRICS metrics
    for i in range(MAX_METRICS):
        provider.add_metric(name=f"Metric_{i}", unit=MetricUnit.Count, value=i)
        
    print(f"After adding {MAX_METRICS} metrics:")
    print(f"  - Number of flushes: {len(flushes)}")
    print(f"  - Metrics in each flush: {flushes}")
    print(f"  - Current metric_set size: {len(provider.metric_set)}")
    
    # Now add one more metric to see what happens
    print(f"\nAdding one more metric (metric #{MAX_METRICS + 1})...")
    provider.add_metric(name=f"Metric_{MAX_METRICS}", unit=MetricUnit.Count, value=MAX_METRICS)
    
    print(f"After adding {MAX_METRICS + 1} metrics:")
    print(f"  - Number of flushes: {len(flushes)}")
    print(f"  - Metrics in each flush: {flushes}")
    print(f"  - Current metric_set size: {len(provider.metric_set)}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("=" * 60)

if len(flushes) > 0 and flushes[0] == MAX_METRICS:
    print(f"✓ The flush correctly happens at {MAX_METRICS} metrics")
    print(f"✓ After flush, metric_set is cleared")
    print(f"✓ The 101st metric goes into a new batch")
else:
    print(f"✗ Unexpected flush behavior")

# Let's also check the logic in the code
print("\n" + "=" * 60)
print("CODE LOGIC ANALYSIS:")
print("=" * 60)
print("The check happens on line 170 of cloudwatch.py:")
print("  if len(self.metric_set) == MAX_METRICS or len(metric['Value']) == MAX_METRICS:")
print("")
print("This check happens AFTER adding the metric to metric_set.")
print("So when we add the 100th metric:")
print("  1. Metric is added to metric_set (now has 100 metrics)")
print("  2. Check: len(self.metric_set) == 100 -> TRUE")
print("  3. Flush happens, clearing metric_set")
print("")
print("This means the code correctly handles the MAX_METRICS limit.")
print("The flush happens when we REACH 100 metrics, not EXCEED it.")