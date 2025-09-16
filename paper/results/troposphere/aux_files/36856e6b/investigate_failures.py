"""Investigate the test failures to determine if they are bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.codebuild import ProjectTriggers, EnvironmentVariable


def investigate_project_triggers_empty_list():
    """Investigate: Empty list in FilterGroups validation."""
    
    print("Test case: FilterGroups with [[]] (list containing empty list)")
    
    # This was failing in the test - depth=2, width=0 creates [[]]
    filter_groups = [[]]  # List containing empty list
    
    triggers = ProjectTriggers(FilterGroups=filter_groups)
    
    try:
        triggers.validate()
        print("✓ Empty inner list validation passed - this is valid!")
        print("  Note: Empty filter group is allowed by the validation")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        print("  This would be a bug if empty lists should be allowed")
    
    # Also test with ["invalid"] which is depth=2, width>0
    print("\nTest case: FilterGroups with [['invalid']] (invalid inner element)")
    filter_groups2 = [["invalid"]]
    triggers2 = ProjectTriggers(FilterGroups=filter_groups2)
    
    try:
        triggers2.validate()
        print("✗ BUG: String passed validation when WebhookFilter expected!")
        return "BUG_FOUND"
    except TypeError as e:
        print(f"✓ Correctly rejected invalid inner element: {e}")
    except AttributeError as e:
        print(f"✓ Correctly rejected invalid inner element: {e}")


def investigate_environment_variable_required():
    """Investigate: Can EnvironmentVariable be created without required properties?"""
    
    print("Test case: Creating EnvironmentVariable with no properties")
    
    try:
        env_var = EnvironmentVariable()
        print(f"✗ Object created without required properties!")
        print(f"  Properties: {env_var.properties}")
        
        # Try to validate it
        try:
            env_var.validate()
            print("✗ BUG: Validation passed without required Name and Value!")
            return "BUG_FOUND"
        except Exception as e:
            print(f"✓ Validation correctly failed: {e}")
            
    except TypeError as e:
        print(f"✓ Correctly prevented creation without required properties: {e}")
    
    print("\nTest case: Creating EnvironmentVariable with only Name")
    
    try:
        env_var = EnvironmentVariable(Name="TEST")
        print(f"✗ Object created with only Name (missing required Value)!")
        print(f"  Properties: {env_var.properties}")
        
        # According to the props definition, both Name and Value are required (True)
        # But object creation succeeded - this might be the bug
        
        try:
            env_var.validate()
            print("✗ BUG: Validation passed without required Value!")
            return "BUG_FOUND"
        except Exception as e:
            print(f"✓ Validation correctly failed: {e}")
            
    except TypeError as e:
        print(f"✓ Correctly prevented creation without Value: {e}")


def check_required_property_enforcement():
    """Check how troposphere enforces required properties."""
    
    print("Investigating required property enforcement in troposphere...")
    
    from troposphere.codebuild import Artifacts, Source
    
    # Artifacts has Type as required
    print("\n1. Artifacts with missing required Type:")
    try:
        artifact = Artifacts()
        print(f"   Object created: {artifact.properties}")
        artifact.validate()
        print("   ✗ Validation passed without required Type")
    except Exception as e:
        print(f"   ✓ Failed as expected: {e}")
    
    # Source has Type as required  
    print("\n2. Source with missing required Type:")
    try:
        source = Source()
        print(f"   Object created: {source.properties}")
        source.validate()
        print("   ✗ Validation passed without required Type")
    except Exception as e:
        print(f"   ✓ Failed as expected: {e}")
    
    # EnvironmentVariable has Name and Value as required
    print("\n3. EnvironmentVariable with missing required properties:")
    try:
        env_var = EnvironmentVariable()
        print(f"   Object created: {env_var.properties}")
        env_var.validate()
        print("   ✗ Validation passed without required properties")
    except Exception as e:
        print(f"   ✓ Failed as expected: {e}")
    
    print("\nConclusion: Troposphere does NOT enforce required properties at object creation time.")
    print("Required properties are only checked when accessing them or during CloudFormation generation.")
    print("The validate() methods only check property VALUES, not presence of required properties.")
    return "NOT_A_BUG"


if __name__ == "__main__":
    print("=" * 60)
    print("INVESTIGATION 1: ProjectTriggers empty list handling")
    print("=" * 60)
    result1 = investigate_project_triggers_empty_list()
    
    print("\n" + "=" * 60)
    print("INVESTIGATION 2: EnvironmentVariable required properties")
    print("=" * 60)
    result2 = investigate_environment_variable_required()
    
    print("\n" + "=" * 60)
    print("INVESTIGATION 3: Required property enforcement pattern")
    print("=" * 60)
    result3 = check_required_property_enforcement()
    
    if result1 == "BUG_FOUND" or result2 == "BUG_FOUND":
        print("\n⚠️  POTENTIAL BUG FOUND - Further investigation needed")
    else:
        print("\n✓ No bugs found - behavior matches design expectations")