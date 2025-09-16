#!/usr/bin/env python3
"""Simple direct test of troposphere.greengrassv2."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.greengrassv2 as ggv2
from troposphere.validators import boolean, integer, double

# Quick manual tests
print("Testing troposphere.greengrassv2 module...")

# Test 1: Boolean validator
print("\n1. Testing boolean validator...")
try:
    assert boolean(True) == True
    assert boolean(False) == False
    assert boolean(1) == True
    assert boolean(0) == False
    assert boolean("true") == True
    assert boolean("false") == False
    print("   ✓ Valid boolean inputs work")
except Exception as e:
    print(f"   ✗ Boolean validator failed: {e}")

# Test invalid boolean
try:
    boolean("invalid")
    print("   ✗ Boolean validator should reject invalid input")
except ValueError:
    print("   ✓ Invalid boolean inputs rejected")

# Test 2: Integer validator
print("\n2. Testing integer validator...")
try:
    assert integer(42) == 42
    assert integer("123") == "123"
    assert integer(-5) == -5
    print("   ✓ Valid integer inputs work")
except Exception as e:
    print(f"   ✗ Integer validator failed: {e}")

# Test invalid integer
try:
    integer("not_a_number")
    print("   ✗ Integer validator should reject invalid input")
except ValueError:
    print("   ✓ Invalid integer inputs rejected")

# Test 3: Double validator
print("\n3. Testing double validator...")
try:
    assert double(3.14) == 3.14
    assert double(42) == 42
    assert double("3.14") == "3.14"
    print("   ✓ Valid double inputs work")
except Exception as e:
    print(f"   ✗ Double validator failed: {e}")

# Test 4: ComponentPlatform construction
print("\n4. Testing ComponentPlatform...")
try:
    platform = ggv2.ComponentPlatform(
        Name="Linux",
        Attributes={"os": "linux", "architecture": "x86_64"}
    )
    result = platform.to_dict()
    assert result['Name'] == "Linux"
    assert result['Attributes']['os'] == "linux"
    print("   ✓ ComponentPlatform construction works")
except Exception as e:
    print(f"   ✗ ComponentPlatform failed: {e}")

# Test 5: SystemResourceLimits
print("\n5. Testing SystemResourceLimits...")
try:
    limits = ggv2.SystemResourceLimits(
        Cpus=2.5,
        Memory=1024
    )
    result = limits.to_dict()
    assert result['Cpus'] == 2.5
    assert result['Memory'] == 1024
    print("   ✓ SystemResourceLimits works")
except Exception as e:
    print(f"   ✗ SystemResourceLimits failed: {e}")

# Test 6: IoTJobAbortCriteria required properties
print("\n6. Testing IoTJobAbortCriteria...")
try:
    criteria = ggv2.IoTJobAbortCriteria(
        Action="CANCEL",
        FailureType="FAILED",
        MinNumberOfExecutedThings=1,
        ThresholdPercentage=50.0
    )
    result = criteria.to_dict()
    assert result['Action'] == "CANCEL"
    print("   ✓ IoTJobAbortCriteria works")
except Exception as e:
    print(f"   ✗ IoTJobAbortCriteria failed: {e}")

# Test 7: Missing required property
print("\n7. Testing missing required property...")
try:
    # Try to create IoTJobAbortCriteria without required Action
    criteria = ggv2.IoTJobAbortCriteria(
        FailureType="FAILED",
        MinNumberOfExecutedThings=1,
        ThresholdPercentage=50.0
    )
    # Call to_dict to trigger validation
    criteria.to_dict()
    print("   ✗ Should have failed validation for missing required property")
except Exception as e:
    print(f"   ✓ Correctly rejected missing required property: {type(e).__name__}")

# Test 8: ComponentVersion AWSObject
print("\n8. Testing ComponentVersion (AWSObject)...")
try:
    component = ggv2.ComponentVersion(
        title="MyComponent",
        InlineRecipe='{"RecipeFormatVersion": "2020-01-25"}',
        Tags={"Environment": "Test"}
    )
    result = component.to_dict()
    assert result['Type'] == 'AWS::GreengrassV2::ComponentVersion'
    print("   ✓ ComponentVersion AWSObject works")
except Exception as e:
    print(f"   ✗ ComponentVersion failed: {e}")

# Test 9: Deployment with required TargetArn
print("\n9. Testing Deployment...")
try:
    deployment = ggv2.Deployment(
        title="MyDeployment",
        TargetArn="arn:aws:greengrass:us-west-2:123456789012:coreDevices:MyCore",
        DeploymentName="TestDeployment"
    )
    result = deployment.to_dict()
    assert result['Type'] == 'AWS::GreengrassV2::Deployment'
    assert result['Properties']['TargetArn'] == "arn:aws:greengrass:us-west-2:123456789012:coreDevices:MyCore"
    print("   ✓ Deployment works")
except Exception as e:
    print(f"   ✗ Deployment failed: {e}")

# Test 10: Complex nested structure
print("\n10. Testing nested objects...")
try:
    limits = ggv2.SystemResourceLimits(Cpus=1.5, Memory=512)
    run_with = ggv2.ComponentRunWith(
        PosixUser="ggc_user",
        SystemResourceLimits=limits
    )
    spec = ggv2.ComponentDeploymentSpecification(
        ComponentVersion="1.0.0",
        RunWith=run_with
    )
    result = spec.to_dict()
    assert result['RunWith']['SystemResourceLimits']['Cpus'] == 1.5
    print("   ✓ Nested object structure works")
except Exception as e:
    print(f"   ✗ Nested objects failed: {e}")

print("\n" + "="*50)
print("Basic testing complete!")