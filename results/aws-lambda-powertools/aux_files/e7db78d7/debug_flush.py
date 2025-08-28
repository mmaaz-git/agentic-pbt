#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider
from aws_lambda_powertools.metrics import MetricUnit
import json

# Let's directly call the code and see what happens
provider = AmazonCloudWatchEMFProvider(namespace="TestNamespace")

print("Adding 100 metrics one by one...")
print("-" * 50)

# Add 100 metrics and track when flush happens
for i in range(100):
    print(f"\nAdding metric #{i+1}")
    print(f"  Before: metric_set size = {len(provider.metric_set)}")
    
    # This is what add_metric does
    name = f"Metric_{i}"
    unit = MetricUnit.Count
    value = i
    
    # Add the metric (simplified version of what add_metric does)
    metric = provider.metric_set.get(name, {"Value": []})
    metric["Unit"] = unit.value
    metric["StorageResolution"] = 60
    metric["Value"].append(float(value))
    provider.metric_set[name] = metric
    
    print(f"  After: metric_set size = {len(provider.metric_set)}")
    
    # Check the condition from line 170
    if len(provider.metric_set) == 100 or len(metric["Value"]) == 100:
        print(f"  *** FLUSH CONDITION MET! ***")
        print(f"      len(metric_set) = {len(provider.metric_set)}")
        print(f"      len(metric['Value']) = {len(metric['Value'])}")
        
        # This is what should happen
        metrics = provider.serialize_metric_set()
        print(f"  *** Serialized {len(metrics['_aws']['CloudWatchMetrics'][0]['Metrics'])} metrics")
        # In real code, it would: print(json.dumps(metrics))
        # Then clear: provider.metric_set.clear()
        
        # Let's see what the real add_metric does
        break

print("\n" + "=" * 50)
print("Now let's call the actual add_metric and see...")
print("=" * 50)

# Create a fresh provider
provider2 = AmazonCloudWatchEMFProvider(namespace="TestNamespace")

# Monkey-patch print to capture output
original_print = print
flush_count = [0]

def capturing_print(*args, **kwargs):
    if args and isinstance(args[0], str) and args[0].startswith('{'):
        flush_count[0] += 1
        original_print(f"*** FLUSH #{flush_count[0]} DETECTED ***")
    else:
        original_print(*args, **kwargs)

import builtins
builtins.print = capturing_print

# Add 100 metrics using the actual method
for i in range(100):
    provider2.add_metric(name=f"M{i}", unit=MetricUnit.Count, value=i)

# Restore print
builtins.print = original_print

print(f"\nTotal flushes detected: {flush_count[0]}")
print(f"Final metric_set size: {len(provider2.metric_set)}")