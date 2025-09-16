"""Focused bug hunting for troposphere.identitystore."""

import sys
import json
import traceback
from hypothesis import given, strategies as st, settings, example

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.identitystore import Group, GroupMembership, MemberId


# Test for potential edge cases and bugs

def test_empty_string_properties():
    """Test what happens with empty strings for required properties."""
    print("\n1. Testing empty strings for required properties...")
    try:
        # Empty string for DisplayName (required)
        group = Group(
            title="TestGroup",
            DisplayName="",  # Empty string - is this valid?
            IdentityStoreId="store-123"
        )
        result = group.to_dict()
        print(f"   Empty DisplayName accepted: {result['Properties']['DisplayName']}")
        # This might be a bug if AWS doesn't accept empty display names
        return "POTENTIAL_BUG: Empty string accepted for DisplayName"
    except Exception as e:
        print(f"   Empty DisplayName rejected: {e}")
        return None


def test_special_characters_in_values():
    """Test special characters that might cause issues."""
    print("\n2. Testing special characters in property values...")
    test_cases = [
        ("Unicode", "Test™Group", "store-123"),
        ("Newline", "Test\nGroup", "store-123"),
        ("Tab", "Test\tGroup", "store-123"),
        ("Null byte", "Test\x00Group", "store-123"),
        ("JSON special", 'Test"Group', "store-123"),
        ("Backslash", "Test\\Group", "store-123"),
    ]
    
    issues = []
    for name, display_name, store_id in test_cases:
        try:
            group = Group(
                title="TestGroup",
                DisplayName=display_name,
                IdentityStoreId=store_id
            )
            json_str = group.to_json()
            # Try to parse it back
            parsed = json.loads(json_str)
            
            # Check if the value roundtrips correctly
            if parsed['Properties']['DisplayName'] != display_name:
                issues.append(f"{name}: Value changed from {repr(display_name)} to {repr(parsed['Properties']['DisplayName'])}")
        except Exception as e:
            print(f"   {name} caused error: {e}")
    
    if issues:
        return f"POTENTIAL_BUG: Special character issues: {issues}"
    return None


def test_member_id_dict_vs_object():
    """Test if MemberId can be passed as dict instead of object."""
    print("\n3. Testing MemberId as dict vs object...")
    try:
        # Try passing dict directly instead of MemberId object
        membership = GroupMembership(
            title="TestMembership",
            GroupId="group-123",
            IdentityStoreId="store-123",
            MemberId={"UserId": "user-456"}  # Dict instead of MemberId object
        )
        result = membership.to_dict()
        print(f"   Dict accepted for MemberId: {result['Properties']['MemberId']}")
        
        # Compare with object version
        member_obj = MemberId(UserId="user-456")
        membership2 = GroupMembership(
            title="TestMembership2",
            GroupId="group-123",
            IdentityStoreId="store-123",
            MemberId=member_obj
        )
        result2 = membership2.to_dict()
        
        if result['Properties']['MemberId'] != result2['Properties']['MemberId']:
            return f"POTENTIAL_BUG: Dict and object produce different results"
            
    except Exception as e:
        print(f"   Error with dict MemberId: {e}")
    
    return None


def test_extremely_long_strings():
    """Test very long strings that might cause issues."""
    print("\n4. Testing extremely long strings...")
    try:
        # Create a very long display name
        long_name = "A" * 10000
        group = Group(
            title="TestGroup",
            DisplayName=long_name,
            IdentityStoreId="store-123"
        )
        json_str = group.to_json()
        
        # Check if it serializes correctly
        parsed = json.loads(json_str)
        if len(parsed['Properties']['DisplayName']) != 10000:
            return f"BUG: Long string truncated from 10000 to {len(parsed['Properties']['DisplayName'])}"
            
    except Exception as e:
        print(f"   Long string caused error: {e}")
    
    return None


def test_property_override():
    """Test if properties can be overridden after creation."""
    print("\n5. Testing property override behavior...")
    try:
        group = Group(
            title="TestGroup",
            DisplayName="Original",
            IdentityStoreId="store-123"
        )
        
        # Try to change DisplayName
        group.DisplayName = "Modified"
        
        result = group.to_dict()
        if result['Properties']['DisplayName'] != "Modified":
            return f"BUG: Property override didn't work, still shows {result['Properties']['DisplayName']}"
        
        # Try setting invalid type after creation
        try:
            group.DisplayName = 123
            return "BUG: Type validation not enforced on property override"
        except TypeError:
            pass  # Expected
            
    except Exception as e:
        print(f"   Property override error: {e}")
    
    return None


def test_none_for_optional_property():
    """Test None value for optional Description property."""
    print("\n6. Testing None for optional property...")
    try:
        group = Group(
            title="TestGroup",
            DisplayName="Test",
            IdentityStoreId="store-123",
            Description=None
        )
        result = group.to_dict()
        
        # Check if None is in the output
        if 'Description' in result['Properties'] and result['Properties']['Description'] is None:
            return "POTENTIAL_BUG: None value included in output instead of being omitted"
            
    except Exception as e:
        print(f"   None value error: {e}")
    
    return None


def test_duplicate_property_in_kwargs():
    """Test what happens with duplicate properties."""
    print("\n7. Testing duplicate properties...")
    try:
        # This might cause issues if not handled properly
        group = Group(
            title="TestGroup",
            DisplayName="First",
            IdentityStoreId="store-123",
            # Can't actually pass duplicate kwargs in Python, but let's test reassignment
        )
        
        # Set it again
        group.DisplayName = "Second"
        result = group.to_dict()
        
        if result['Properties']['DisplayName'] != "Second":
            return f"BUG: Property reassignment failed"
            
    except Exception as e:
        print(f"   Duplicate property error: {e}")
    
    return None


def test_serialization_with_circular_reference():
    """Test if circular references cause issues."""
    print("\n8. Testing circular reference handling...")
    try:
        member = MemberId(UserId="user-123")
        
        # Try to create a weird circular structure (shouldn't be possible but let's try)
        # This is more of a robustness test
        membership = GroupMembership(
            title="TestMembership",
            GroupId="group-123",
            IdentityStoreId="store-123",
            MemberId=member
        )
        
        # Try to set membership as its own property (shouldn't work)
        try:
            membership.weird_prop = membership
            json_str = membership.to_json()
            return "BUG: Circular reference not detected"
        except:
            pass  # Expected to fail
            
    except Exception as e:
        print(f"   Circular reference error: {e}")
    
    return None


def test_from_dict_roundtrip():
    """Test _from_dict method for round-trip property."""
    print("\n9. Testing _from_dict round-trip...")
    try:
        # Create a group
        group = Group(
            title="TestGroup",
            DisplayName="Test Display",
            IdentityStoreId="store-123",
            Description="Test Description"
        )
        
        # Convert to dict
        group_dict = group.to_dict()
        
        # Try to reconstruct from properties dict
        # Note: _from_dict is a class method
        props = group_dict['Properties']
        
        # Try to create new group from dict
        new_group = Group._from_dict(title="TestGroup2", **props)
        new_dict = new_group.to_dict()
        
        # Compare the Properties sections
        if group_dict['Properties'] != new_dict['Properties']:
            return f"BUG: Round-trip failed, properties differ"
            
    except Exception as e:
        print(f"   Round-trip error: {e}")
        traceback.print_exc()
    
    return None


# Run all tests
if __name__ == "__main__":
    print("=" * 60)
    print("Bug Hunting for troposphere.identitystore")
    print("=" * 60)
    
    bugs_found = []
    
    tests = [
        test_empty_string_properties,
        test_special_characters_in_values,
        test_member_id_dict_vs_object,
        test_extremely_long_strings,
        test_property_override,
        test_none_for_optional_property,
        test_duplicate_property_in_kwargs,
        test_serialization_with_circular_reference,
        test_from_dict_roundtrip,
    ]
    
    for test_func in tests:
        result = test_func()
        if result:
            bugs_found.append(result)
    
    print("\n" + "=" * 60)
    if bugs_found:
        print("POTENTIAL BUGS FOUND:")
        for i, bug in enumerate(bugs_found, 1):
            print(f"{i}. {bug}")
    else:
        print("No bugs found - all tests passed!")
    print("=" * 60)