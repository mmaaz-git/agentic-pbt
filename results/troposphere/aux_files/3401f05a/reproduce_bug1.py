#!/usr/bin/env python3
"""Minimal reproduction for IntegerHyperParameterRange bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import personalize, Template
import json

# Bug: IntegerHyperParameterRange accepts MaxValue < MinValue
# This violates the fundamental property of a range

# Create an invalid range where max < min
invalid_range = personalize.IntegerHyperParameterRange(
    Name='epochs',
    MinValue=100,
    MaxValue=10  # Should not be allowed: max < min
)

print("Created IntegerHyperParameterRange with MinValue=100, MaxValue=10")
print("to_dict():", invalid_range.to_dict())
print()

# This gets worse when used in a CloudFormation template
template = Template()
solution = personalize.Solution(
    'MySolution',
    DatasetGroupArn='arn:aws:personalize:us-east-1:123456789012:dataset-group/test',
    Name='MySolution', 
    SolutionConfig=personalize.SolutionConfig(
        HpoConfig=personalize.HpoConfig(
            AlgorithmHyperParameterRanges=personalize.AlgorithmHyperParameterRanges(
                IntegerHyperParameterRanges=[invalid_range]
            )
        )
    )
)
template.add_resource(solution)

# The generated CloudFormation will have invalid configuration
output = json.loads(template.to_json())
range_in_template = output['Resources']['MySolution']['Properties']['SolutionConfig']['HpoConfig']['AlgorithmHyperParameterRanges']['IntegerHyperParameterRanges'][0]

print("Generated CloudFormation template with invalid range:")
print(f"  MinValue: {range_in_template['MinValue']}")
print(f"  MaxValue: {range_in_template['MaxValue']}")
print()
print("AWS Personalize would reject this configuration as invalid.")