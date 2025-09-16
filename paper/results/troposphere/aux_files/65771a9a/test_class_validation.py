"""Test validation at the class level in troposphere.appconfig"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import appconfig
from hypothesis import given, strategies as st, assume

print("Testing class-level validation in troposphere.appconfig...")
print("=" * 70)

bugs_found = []

# Test 1: Test Validators class with invalid Type
print("\n[TEST 1] Testing Validators class with invalid Type...")
try:
    # Try to create Validators with invalid type
    validator = appconfig.Validators(
        Type="INVALID_TYPE",
        Content="test content"
    )
    # Try to convert to dict (this usually triggers validation)
    try:
        result = validator.to_dict()
        print(f"✗ Validators.to_dict() succeeded with invalid Type: {result}")
        bugs_found.append("Validators accepts invalid Type in to_dict()")
    except ValueError as e:
        print(f"✓ Validators.to_dict() correctly rejected invalid Type: {e}")
    except AttributeError:
        # Try with JSONrepr if to_dict doesn't exist
        try:
            result = validator.JSONrepr()
            print(f"✗ Validators.JSONrepr() succeeded with invalid Type: {result}")
            bugs_found.append("Validators accepts invalid Type in JSONrepr()")
        except ValueError as e:
            print(f"✓ Validators.JSONrepr() correctly rejected invalid Type")
        except AttributeError:
            print("  Note: Neither to_dict() nor JSONrepr() methods found")
except Exception as e:
    print(f"  Validators creation raised: {type(e).__name__}: {e}")

# Test 2: Test DeploymentStrategy with invalid GrowthType
print("\n[TEST 2] Testing DeploymentStrategy with invalid GrowthType...")
try:
    strategy = appconfig.DeploymentStrategy(
        "TestStrategy",
        DeploymentDurationInMinutes=1.0,
        GrowthFactor=1.0,
        GrowthType="EXPONENTIAL",  # Invalid - only LINEAR is valid
        Name="test",
        ReplicateTo="NONE"
    )
    try:
        result = strategy.to_dict()
        print(f"✗ DeploymentStrategy.to_dict() succeeded with invalid GrowthType: {result}")
        bugs_found.append("DeploymentStrategy accepts invalid GrowthType in to_dict()")
    except ValueError as e:
        print(f"✓ DeploymentStrategy.to_dict() correctly rejected invalid GrowthType: {e}")
    except AttributeError:
        try:
            result = strategy.JSONrepr()
            print(f"✗ DeploymentStrategy.JSONrepr() succeeded with invalid GrowthType")
            bugs_found.append("DeploymentStrategy accepts invalid GrowthType in JSONrepr()")
        except ValueError as e:
            print(f"✓ DeploymentStrategy.JSONrepr() correctly rejected invalid GrowthType")
        except AttributeError:
            print("  Note: Neither to_dict() nor JSONrepr() methods found")
except Exception as e:
    print(f"  DeploymentStrategy creation raised: {type(e).__name__}: {e}")

# Test 3: Test DeploymentStrategy with invalid ReplicateTo
print("\n[TEST 3] Testing DeploymentStrategy with invalid ReplicateTo...")
try:
    strategy = appconfig.DeploymentStrategy(
        "TestStrategy2",
        DeploymentDurationInMinutes=1.0,
        GrowthFactor=1.0,
        GrowthType="LINEAR",
        Name="test2",
        ReplicateTo="S3_BUCKET"  # Invalid - only NONE or SSM_DOCUMENT
    )
    try:
        result = strategy.to_dict()
        print(f"✗ DeploymentStrategy.to_dict() succeeded with invalid ReplicateTo: {result}")
        bugs_found.append("DeploymentStrategy accepts invalid ReplicateTo in to_dict()")
    except ValueError as e:
        print(f"✓ DeploymentStrategy.to_dict() correctly rejected invalid ReplicateTo: {e}")
    except AttributeError:
        try:
            result = strategy.JSONrepr()
            print(f"✗ DeploymentStrategy.JSONrepr() succeeded with invalid ReplicateTo")
            bugs_found.append("DeploymentStrategy accepts invalid ReplicateTo in JSONrepr()")
        except ValueError as e:
            print(f"✓ DeploymentStrategy.JSONrepr() correctly rejected invalid ReplicateTo")
        except AttributeError:
            print("  Note: Neither to_dict() nor JSONrepr() methods found")
except Exception as e:
    print(f"  DeploymentStrategy creation raised: {type(e).__name__}: {e}")

# Test 4: Test edge cases with None values
print("\n[TEST 4] Testing classes with None values for validated fields...")
try:
    validator = appconfig.Validators(
        Type=None,
        Content="test"
    )
    try:
        result = validator.to_dict()
        # If None is allowed, it should either be omitted or handled properly
        if 'Type' in result and result['Type'] is None:
            print(f"  Validators.to_dict() with Type=None returned: {result}")
        elif 'Type' not in result:
            print(f"  Validators.to_dict() omitted Type when None")
        else:
            print(f"  Validators.to_dict() with Type=None returned: {result}")
    except (ValueError, TypeError) as e:
        print(f"  Validators.to_dict() with Type=None raised: {e}")
    except AttributeError:
        pass
except Exception as e:
    print(f"  Validators creation with Type=None raised: {type(e).__name__}: {e}")

# Test 5: Test with empty strings
print("\n[TEST 5] Testing classes with empty strings for validated fields...")
try:
    strategy = appconfig.DeploymentStrategy(
        "TestStrategy3",
        DeploymentDurationInMinutes=1.0,
        GrowthFactor=1.0,
        GrowthType="",  # Empty string
        Name="test3",
        ReplicateTo="NONE"
    )
    try:
        result = strategy.to_dict()
        print(f"✗ DeploymentStrategy.to_dict() succeeded with empty GrowthType: {result}")
        bugs_found.append("DeploymentStrategy accepts empty string for GrowthType")
    except ValueError as e:
        print(f"✓ DeploymentStrategy.to_dict() correctly rejected empty GrowthType: {e}")
    except AttributeError:
        pass
except Exception as e:
    print(f"  DeploymentStrategy creation with empty GrowthType raised: {type(e).__name__}: {e}")

# Test 6: Test lowercase values
print("\n[TEST 6] Testing classes with lowercase validated values...")
try:
    strategy = appconfig.DeploymentStrategy(
        "TestStrategy4",
        DeploymentDurationInMinutes=1.0,
        GrowthFactor=1.0,
        GrowthType="linear",  # lowercase
        Name="test4",
        ReplicateTo="none"  # lowercase
    )
    try:
        result = strategy.to_dict()
        print(f"✗ DeploymentStrategy.to_dict() succeeded with lowercase values: {result}")
        bugs_found.append("DeploymentStrategy accepts lowercase validated values")
    except ValueError as e:
        print(f"✓ DeploymentStrategy.to_dict() correctly rejected lowercase values: {e}")
    except AttributeError:
        pass
except Exception as e:
    print(f"  DeploymentStrategy creation with lowercase values raised: {type(e).__name__}: {e}")

# Summary
print("\n" + "=" * 70)
if bugs_found:
    print(f"❌ Found {len(bugs_found)} potential issues:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("✅ All class-level validation tests passed!")

print("\nClass validation aspects tested:")
print("1. Invalid Type in Validators class")
print("2. Invalid GrowthType in DeploymentStrategy")
print("3. Invalid ReplicateTo in DeploymentStrategy")
print("4. None values for validated fields")
print("5. Empty strings for validated fields")
print("6. Lowercase values for case-sensitive fields")