#!/usr/bin/env python3
"""Property-based tests for troposphere.personalize module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import troposphere.personalize as personalize
import json


# Test 1: IntegerHyperParameterRange should have MaxValue >= MinValue
@given(
    name=st.text(min_size=1, max_size=50),
    min_val=st.integers(min_value=-1000000, max_value=1000000),
    max_val=st.integers(min_value=-1000000, max_value=1000000)
)
def test_integer_hyperparameter_range_invariant(name, min_val, max_val):
    """
    Test that IntegerHyperParameterRange maintains the invariant MaxValue >= MinValue.
    
    This is a fundamental property of any range - the maximum should not be less than minimum.
    AWS Personalize would reject such invalid ranges.
    """
    obj = personalize.IntegerHyperParameterRange(
        Name=name,
        MinValue=min_val,
        MaxValue=max_val
    )
    
    # Get the dictionary representation
    result = obj.to_dict()
    
    # If both values are present, max should be >= min
    if 'MinValue' in result and 'MaxValue' in result:
        min_value = result['MinValue']
        max_value = result['MaxValue']
        
        # This is the property that should hold but doesn't
        # The library should either:
        # 1. Raise an error when MaxValue < MinValue, or
        # 2. Automatically swap them to maintain the invariant
        assert max_value >= min_value, f"MaxValue ({max_value}) should be >= MinValue ({min_value})"


# Test 2: ContinuousHyperParameterRange should have MaxValue >= MinValue  
@given(
    name=st.text(min_size=1, max_size=50),
    min_val=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_continuous_hyperparameter_range_invariant(name, min_val, max_val):
    """
    Test that ContinuousHyperParameterRange maintains the invariant MaxValue >= MinValue.
    
    Similar to integer ranges, continuous ranges should maintain max >= min.
    """
    obj = personalize.ContinuousHyperParameterRange(
        Name=name,
        MinValue=min_val,
        MaxValue=max_val
    )
    
    result = obj.to_dict()
    
    if 'MinValue' in result and 'MaxValue' in result:
        min_value = result['MinValue']
        max_value = result['MaxValue']
        
        assert max_value >= min_value, f"MaxValue ({max_value}) should be >= MinValue ({min_value})"


# Test 3: HpoResourceConfig should only accept valid numeric strings
@given(
    max_jobs=st.text(min_size=1, max_size=20),
    max_parallel=st.text(min_size=1, max_size=20)
)
def test_hpo_resource_config_numeric_validation(max_jobs, max_parallel):
    """
    Test that HpoResourceConfig validates that MaxNumberOfTrainingJobs and 
    MaxParallelTrainingJobs are numeric strings representing positive integers.
    
    These fields represent counts and should be positive integers.
    """
    obj = personalize.HpoResourceConfig(
        MaxNumberOfTrainingJobs=max_jobs,
        MaxParallelTrainingJobs=max_parallel
    )
    
    result = obj.to_dict()
    
    # Check if the values are valid positive integer strings
    for field_name, field_value in [
        ('MaxNumberOfTrainingJobs', result.get('MaxNumberOfTrainingJobs')),
        ('MaxParallelTrainingJobs', result.get('MaxParallelTrainingJobs'))
    ]:
        if field_value is not None:
            # Should be convertible to an integer
            try:
                num_value = int(field_value)
                # Should be positive (at least 1)
                assert num_value > 0, f"{field_name} should be positive, got {num_value}"
            except (ValueError, TypeError):
                # Should fail if not a valid number
                raise AssertionError(f"{field_name} should be a numeric string, got '{field_value}'")


# Test 4: Template generation with invalid ranges should be rejected
@given(
    min_val=st.integers(min_value=1, max_value=1000),
    max_val=st.integers(min_value=1, max_value=1000)
)
def test_solution_with_hyperparameter_ranges(min_val, max_val):
    """
    Test that Solutions with hyperparameter ranges maintain valid configurations.
    """
    # Only test when min > max to find the bug
    assume(min_val > max_val)
    
    from troposphere import Template
    
    template = Template()
    
    solution_config = personalize.SolutionConfig(
        HpoConfig=personalize.HpoConfig(
            AlgorithmHyperParameterRanges=personalize.AlgorithmHyperParameterRanges(
                IntegerHyperParameterRanges=[
                    personalize.IntegerHyperParameterRange(
                        Name='test_param',
                        MinValue=min_val,
                        MaxValue=max_val
                    )
                ]
            )
        )
    )
    
    solution = personalize.Solution(
        'TestSolution',
        DatasetGroupArn='arn:aws:personalize:us-east-1:123456789012:dataset-group/test',
        Name='TestSolution',
        SolutionConfig=solution_config
    )
    
    template.add_resource(solution)
    
    # Generate the CloudFormation template
    output = template.to_json()
    parsed = json.loads(output)
    
    # Extract the ranges from the generated template
    ranges = parsed['Resources']['TestSolution']['Properties']['SolutionConfig']['HpoConfig']['AlgorithmHyperParameterRanges']['IntegerHyperParameterRanges'][0]
    
    # The template should not have MaxValue < MinValue
    template_min = ranges['MinValue']
    template_max = ranges['MaxValue']
    
    assert template_max >= template_min, f"Generated template has invalid range: min={template_min}, max={template_max}"


if __name__ == '__main__':
    # Run with pytest for better output
    import pytest
    pytest.main([__file__, '-v'])