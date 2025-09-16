#!/usr/bin/env python3
"""Test demonstrating missing EC2 instance type constants in troposphere.constants."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.constants as tc


def test_m5a_instance_completeness():
    """Test that M5A instance family has all AWS-supported sizes.
    
    According to AWS documentation, the M5A family supports:
    m5a.large, m5a.xlarge, m5a.2xlarge, m5a.4xlarge, 
    m5a.8xlarge, m5a.12xlarge, m5a.16xlarge, m5a.24xlarge
    
    Source: https://aws.amazon.com/ec2/instance-types/m5/
    """
    
    # Expected M5A instance types based on AWS documentation
    expected_m5a_instances = {
        'M5A_LARGE': 'm5a.large',
        'M5A_XLARGE': 'm5a.xlarge', 
        'M5A_2XLARGE': 'm5a.2xlarge',
        'M5A_4XLARGE': 'm5a.4xlarge',
        'M5A_8XLARGE': 'm5a.8xlarge',      # MISSING!
        'M5A_12XLARGE': 'm5a.12xlarge',
        'M5A_16XLARGE': 'm5a.16xlarge',    # MISSING!
        'M5A_24XLARGE': 'm5a.24xlarge'
    }
    
    missing = []
    for const_name, expected_value in expected_m5a_instances.items():
        if hasattr(tc, const_name):
            actual = getattr(tc, const_name)
            assert actual == expected_value, f"{const_name} has wrong value: {actual}"
        else:
            missing.append((const_name, expected_value))
    
    assert len(missing) == 0, f"Missing M5A constants: {missing}"


def test_m5ad_instance_completeness():
    """Test that M5AD instance family has all AWS-supported sizes.
    
    According to AWS documentation, the M5AD family supports:
    m5ad.large, m5ad.xlarge, m5ad.2xlarge, m5ad.4xlarge,
    m5ad.8xlarge, m5ad.12xlarge, m5ad.16xlarge, m5ad.24xlarge
    """
    
    # Expected M5AD instance types
    expected_m5ad_instances = {
        'M5AD_LARGE': 'm5ad.large',
        'M5AD_XLARGE': 'm5ad.xlarge',
        'M5AD_2XLARGE': 'm5ad.2xlarge', 
        'M5AD_4XLARGE': 'm5ad.4xlarge',
        'M5AD_8XLARGE': 'm5ad.8xlarge',     # MISSING!
        'M5AD_12XLARGE': 'm5ad.12xlarge',
        'M5AD_16XLARGE': 'm5ad.16xlarge',   # MISSING!  
        'M5AD_24XLARGE': 'm5ad.24xlarge'
    }
    
    missing = []
    for const_name, expected_value in expected_m5ad_instances.items():
        if hasattr(tc, const_name):
            actual = getattr(tc, const_name)
            assert actual == expected_value, f"{const_name} has wrong value: {actual}"
        else:
            missing.append((const_name, expected_value))
    
    assert len(missing) == 0, f"Missing M5AD constants: {missing}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])