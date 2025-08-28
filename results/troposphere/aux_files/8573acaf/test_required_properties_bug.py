"""Test for required properties validation bug in troposphere.cloudfront"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import pytest
from troposphere import cloudfront

def test_required_properties_not_validated_at_instantiation():
    """
    Bug: Required properties are not validated at object instantiation,
    only when converting to dict/JSON. This violates the principle of
    failing fast and can lead to runtime errors much later in the code.
    """
    
    # DefaultCacheBehavior has two required properties:
    # - TargetOriginId (required=True)  
    # - ViewerProtocolPolicy (required=True)
    
    # BUG: This should raise an error but doesn't
    behavior = cloudfront.DefaultCacheBehavior()
    
    # Object is created successfully without required properties
    assert behavior.properties == {}
    
    # BUG: Error only occurs when trying to serialize
    with pytest.raises(ValueError, match="Resource TargetOriginId required"):
        behavior.to_dict()


def test_partial_required_properties_not_validated():
    """
    Bug: Objects can be created with only some required properties,
    error only occurs during serialization.
    """
    
    # Create with only one of two required properties
    behavior = cloudfront.DefaultCacheBehavior(TargetOriginId="origin1")
    
    # Object created successfully 
    assert behavior.properties == {"TargetOriginId": "origin1"}
    
    # Error only on serialization
    with pytest.raises(ValueError, match="Resource ViewerProtocolPolicy required"):
        behavior.to_dict()


@given(st.text(min_size=1))
def test_cachepolicyconfig_required_properties_bug(name):
    """
    Bug: CachePolicyConfig can be instantiated without required properties.
    It requires DefaultTTL, MaxTTL, MinTTL, Name, and ParametersInCacheKeyAndForwardedToOrigin.
    """
    
    # Create with only Name, missing other required properties
    config = cloudfront.CachePolicyConfig(Name=name)
    
    # Object created successfully
    assert config.properties["Name"] == name
    
    # Should fail when serializing due to missing required properties
    with pytest.raises(ValueError, match="Resource .* required"):
        config.to_dict()


def test_distribution_required_properties_bug():
    """
    Bug: Distribution can be created without required DistributionConfig
    """
    
    # Distribution requires DistributionConfig
    dist = cloudfront.Distribution("TestDist")
    
    # Object created without required property
    assert "DistributionConfig" not in dist.properties
    
    # Error only on serialization
    with pytest.raises(ValueError, match="Resource DistributionConfig required"):
        dist.to_dict()


def test_multiple_classes_with_required_properties():
    """
    Test that multiple CloudFront classes have this bug
    """
    
    # Classes with required properties that don't validate at instantiation
    test_cases = [
        (cloudfront.CachePolicy, ["CachePolicyConfig"]),
        (cloudfront.Function, ["FunctionCode", "FunctionConfig", "Name"]),
        (cloudfront.KeyGroup, ["KeyGroupConfig"]),
        (cloudfront.OriginRequestPolicy, ["OriginRequestPolicyConfig"]),
        (cloudfront.PublicKey, ["PublicKeyConfig"]),
        (cloudfront.ResponseHeadersPolicy, ["ResponseHeadersPolicyConfig"]),
    ]
    
    for cls, required_props in test_cases:
        # Create instance without required properties
        if cls == cloudfront.Function:
            obj = cls("TestName")  # Function requires a name in constructor
        else:
            obj = cls("TestResource")
        
        # Should create successfully (bug)
        assert obj is not None
        
        # Should fail on serialization
        with pytest.raises(ValueError, match="Resource .* required"):
            obj.to_dict()


def test_delayed_validation_causes_issues():
    """
    Demonstrate how delayed validation can cause issues in real usage
    """
    
    # Developer creates objects thinking they're valid
    behaviors = []
    for i in range(5):
        # Oops, forgot ViewerProtocolPolicy
        behavior = cloudfront.DefaultCacheBehavior(
            TargetOriginId=f"origin{i}"
        )
        behaviors.append(behavior)
    
    # Much later in the code, try to use them
    for i, behavior in enumerate(behaviors):
        # This will fail for all behaviors
        with pytest.raises(ValueError, match="Resource ViewerProtocolPolicy required"):
            behavior.to_dict()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])