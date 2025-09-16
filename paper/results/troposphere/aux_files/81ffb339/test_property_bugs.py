#!/usr/bin/env python3
"""Test for potential bugs in property handling of troposphere.mediastore classes."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.mediastore import CorsRule, MetricPolicyRule, MetricPolicy, Container
from troposphere.validators.mediastore import containerlevelmetrics_status

# Test 1: Check if MetricPolicy validates ContainerLevelMetrics properly
@given(
    invalid_status=st.text().filter(lambda x: x not in ["DISABLED", "ENABLED"]),
    rules=st.lists(st.builds(
        MetricPolicyRule,
        ObjectGroup=st.text(min_size=1),
        ObjectGroupName=st.text(min_size=1)
    ), max_size=3)
)
@settings(max_examples=100)
def test_metric_policy_invalid_status(invalid_status, rules):
    """Test if MetricPolicy properly validates ContainerLevelMetrics."""
    # This should raise an error for invalid status
    with pytest.raises(ValueError) as exc_info:
        policy = MetricPolicy(
            ContainerLevelMetrics=invalid_status,
            MetricPolicyRules=rules
        )
        # Try to convert to dict which might trigger validation
        policy.to_dict()
    assert "ContainerLevelMetrics must be one of" in str(exc_info.value)


# Test 2: Check for missing required fields
@given(
    group=st.text(min_size=1),
    name=st.text(min_size=1),
    include_group=st.booleans(),
    include_name=st.booleans()
)
def test_metric_policy_rule_missing_required(group, name, include_group, include_name):
    """Test that MetricPolicyRule enforces required fields."""
    kwargs = {}
    if include_group:
        kwargs["ObjectGroup"] = group
    if include_name:
        kwargs["ObjectGroupName"] = name
    
    if not include_group or not include_name:
        # Should fail if missing required fields
        with pytest.raises((TypeError, KeyError, AttributeError)):
            rule = MetricPolicyRule(**kwargs)
            rule.to_dict()
    else:
        # Should succeed with both fields
        rule = MetricPolicyRule(**kwargs)
        result = rule.to_dict()
        assert result["ObjectGroup"] == group
        assert result["ObjectGroupName"] == name


# Test 3: Check Container title validation
@given(
    title=st.text(),
    container_name=st.text(min_size=1)
)
@settings(max_examples=100)
def test_container_title_validation(title, container_name):
    """Test Container title validation rules."""
    try:
        container = Container(
            title=title,
            ContainerName=container_name
        )
        # Title should follow AWS naming rules (alphanumeric only)
        # Check if validation is actually enforced
        if title and not title.replace('_', '').replace('-', '').isalnum():
            # This might be a bug if it doesn't raise an error
            print(f"Potential bug: Container accepted invalid title: {repr(title)}")
    except (ValueError, TypeError) as e:
        # Expected for invalid titles
        pass


# Test 4: Test MaxAgeSeconds integer validation in CorsRule
@given(
    max_age=st.one_of(
        st.floats(),
        st.text(),
        st.lists(st.integers()),
        st.none()
    )
)
def test_cors_rule_max_age_validation(max_age):
    """Test that CorsRule validates MaxAgeSeconds as integer."""
    try:
        # Skip actual integers
        if isinstance(max_age, int):
            assume(False)
        try:
            int(max_age)
            assume(False)  # Skip if convertible to int
        except (ValueError, TypeError):
            pass
        
        cors = CorsRule(MaxAgeSeconds=max_age)
        result = cors.to_dict()
        
        # If we got here with non-integer, it might be a bug
        print(f"Potential bug: CorsRule accepted non-integer MaxAgeSeconds: {repr(max_age)}")
        print(f"Result: {result}")
        
    except (ValueError, TypeError, AttributeError) as e:
        # Expected for non-integers
        pass


# Test 5: Property type preservation
@given(
    headers=st.lists(st.text()),
    max_age=st.integers(min_value=0, max_value=86400)
)
def test_cors_rule_type_preservation(headers, max_age):
    """Test that CorsRule preserves types correctly."""
    cors = CorsRule(
        AllowedHeaders=headers,
        MaxAgeSeconds=max_age
    )
    
    result = cors.to_dict()
    
    # Check if types are preserved
    if "AllowedHeaders" in result:
        assert isinstance(result["AllowedHeaders"], list)
        assert result["AllowedHeaders"] == headers
    
    if "MaxAgeSeconds" in result:
        # Should be the same integer
        assert result["MaxAgeSeconds"] == max_age
        assert type(result["MaxAgeSeconds"]) == type(max_age)


if __name__ == "__main__":
    print("Running property-based tests for troposphere.mediastore...")
    
    # Run tests individually to catch specific issues
    print("\n1. Testing MetricPolicy status validation...")
    try:
        test_metric_policy_invalid_status()
        print("   ✓ Test passed")
    except AssertionError as e:
        print(f"   ✗ Test failed: {e}")
    
    print("\n2. Testing MetricPolicyRule required fields...")
    try:
        test_metric_policy_rule_missing_required()
        print("   ✓ Test passed")
    except AssertionError as e:
        print(f"   ✗ Test failed: {e}")
    
    print("\n3. Testing Container title validation...")
    try:
        test_container_title_validation()
        print("   ✓ Test passed")
    except AssertionError as e:
        print(f"   ✗ Test failed: {e}")
    
    print("\n4. Testing CorsRule MaxAgeSeconds validation...")
    try:
        test_cors_rule_max_age_validation()
        print("   ✓ Test passed")
    except AssertionError as e:
        print(f"   ✗ Test failed: {e}")
    
    print("\n5. Testing CorsRule type preservation...")
    try:
        test_cors_rule_type_preservation()
        print("   ✓ Test passed")
    except AssertionError as e:
        print(f"   ✗ Test failed: {e}")
    
    print("\nRunning all tests with pytest...")
    pytest.main([__file__, "-v", "--tb=short"])