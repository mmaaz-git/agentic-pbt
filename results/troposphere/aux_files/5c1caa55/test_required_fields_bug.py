"""Demonstrate the required fields validation bug in troposphere.autoscalingplans"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import pytest
from troposphere.autoscalingplans import (
    TagFilter, MetricDimension, ApplicationSource,
    CustomizedLoadMetricSpecification, PredefinedLoadMetricSpecification,
    CustomizedScalingMetricSpecification, PredefinedScalingMetricSpecification,
    TargetTrackingConfiguration, ScalingInstruction, ScalingPlan
)

# Property: Classes with required fields should fail at instantiation, not at to_dict()
def test_required_fields_deferred_validation_bug():
    """
    Classes allow instantiation without required fields but fail later at to_dict().
    This violates fail-fast principle - errors should happen at instantiation.
    """
    
    test_cases = [
        (TagFilter, ["Key"]),
        (MetricDimension, ["Name", "Value"]),
        (CustomizedLoadMetricSpecification, ["MetricName", "Namespace", "Statistic"]),
        (PredefinedLoadMetricSpecification, ["PredefinedLoadMetricType"]),
        (CustomizedScalingMetricSpecification, ["MetricName", "Namespace", "Statistic"]),
        (PredefinedScalingMetricSpecification, ["PredefinedScalingMetricType"]),
        (TargetTrackingConfiguration, ["TargetValue"]),
        (ScalingInstruction, ["MaxCapacity", "MinCapacity", "ResourceId", 
                              "ScalableDimension", "ServiceNamespace", 
                              "TargetTrackingConfigurations"]),
        (ScalingPlan, ["ApplicationSource", "ScalingInstructions"])
    ]
    
    failures = []
    
    for cls, required_fields in test_cases:
        # Step 1: Create instance without required fields - should fail but doesn't
        try:
            instance = cls()
            # If we get here, instantiation succeeded (bug!)
            
            # Step 2: Try to use the instance - this is where it fails
            try:
                result = instance.to_dict()
                # If this succeeds, the field wasn't actually required
                failures.append(f"{cls.__name__}: Created and used without required fields {required_fields}")
            except Exception as e:
                # This is the bug: validation happens at to_dict(), not at instantiation
                failures.append(f"{cls.__name__}: Allows creation without {required_fields}, fails at to_dict() with: {str(e)[:100]}")
        except (TypeError, KeyError, ValueError) as e:
            # This would be correct behavior - fail at instantiation
            pass
    
    return failures


# Run the test and print results
print("Testing required fields validation bug...\n")
failures = test_required_fields_deferred_validation_bug()

if failures:
    print("BUG FOUND: Classes defer required field validation until to_dict():\n")
    for failure in failures:
        print(f"  - {failure}")
    print("\nThis violates the fail-fast principle. Validation should happen at instantiation.")
else:
    print("No bug found - all classes properly validate required fields at instantiation")


# Additional test: Demonstrate the impact with a realistic scenario
def test_bug_impact_scenario():
    """Show how this bug could affect real users"""
    print("\n\nDemonstrating real-world impact:")
    print("-" * 50)
    
    # Developer creates a TagFilter, forgetting the required Key
    print("1. Developer creates TagFilter without required Key:")
    tf = TagFilter()  # This should fail but doesn't
    print("   TagFilter created successfully (shouldn't happen!)")
    
    # Developer continues building their template
    print("\n2. Developer adds it to ApplicationSource:")
    app_source = ApplicationSource(TagFilters=[tf])
    print("   ApplicationSource created with invalid TagFilter")
    
    # Much later, when trying to generate the CloudFormation template...
    print("\n3. Later, when generating CloudFormation template:")
    try:
        result = app_source.to_dict()
        print(f"   Success: {result}")
    except Exception as e:
        print(f"   FAILURE: {e}")
        print("\n   The error happens far from where the mistake was made!")


test_bug_impact_scenario()