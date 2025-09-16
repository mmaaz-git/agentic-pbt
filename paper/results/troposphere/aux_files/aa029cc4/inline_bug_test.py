#!/usr/bin/env python3
"""Inline bug testing for troposphere.identitystore"""

import sys
import json
import traceback

# Add path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import and test inline
exec("""
from troposphere.identitystore import Group, GroupMembership, MemberId

print("Testing troposphere.identitystore for bugs...")
print("=" * 60)

# BUG HUNT 1: Test if isinstance check is correct for MemberId
print("\\nBUG TEST 1: MemberId type validation")
try:
    # According to the props, MemberId should be of type MemberId
    # Let's test if we can pass a dict instead
    membership = GroupMembership(
        title="Test",
        GroupId="g-123",
        IdentityStoreId="s-123",
        MemberId={"UserId": "u-123"}  # Dict instead of MemberId object
    )
    result = membership.to_dict()
    print("  POTENTIAL BUG: Dict accepted for MemberId property!")
    print(f"  Result: {result['Properties']['MemberId']}")
    bug1 = True
except TypeError as e:
    print(f"  OK: Type validation working - {e}")
    bug1 = False

# BUG TEST 2: Empty required string validation
print("\\nBUG TEST 2: Empty string for required properties")
try:
    group = Group(
        title="Test",
        DisplayName="",  # Empty string - should this be valid?
        IdentityStoreId="s-123"
    )
    result = group.to_dict()
    print("  POTENTIAL BUG: Empty string accepted for required DisplayName!")
    print(f"  DisplayName value: '{result['Properties']['DisplayName']}'")
    bug2 = True
except (ValueError, TypeError) as e:
    print(f"  OK: Empty string rejected - {e}")
    bug2 = False

# BUG TEST 3: None handling for optional properties
print("\\nBUG TEST 3: None value for optional Description")
try:
    group = Group(
        title="Test",
        DisplayName="TestDisplay",
        IdentityStoreId="s-123",
        Description=None
    )
    result = group.to_dict()
    if 'Description' in result['Properties']:
        if result['Properties']['Description'] is None:
            print("  POTENTIAL BUG: None included in JSON output!")
            print(f"  Description: {result['Properties']['Description']}")
            bug3 = True
        else:
            print("  OK: None handled properly")
            bug3 = False
    else:
        print("  OK: None property omitted from output")
        bug3 = False
except Exception as e:
    print(f"  Error: {e}")
    bug3 = False

# BUG TEST 4: Special characters in JSON serialization
print("\\nBUG TEST 4: Special characters in strings")
special_cases = [
    ('Quotes', 'Test"Quote'),
    ('Newline', 'Test\\nNewline'),
    ('Tab', 'Test\\tTab'),
    ('Backslash', 'Test\\\\Backslash'),
    ('Unicode', 'Test™Unicode'),
]

bug4 = False
for name, value in special_cases:
    try:
        group = Group(
            title="Test",
            DisplayName=value,
            IdentityStoreId="s-123"
        )
        json_str = group.to_json()
        parsed = json.loads(json_str)
        if parsed['Properties']['DisplayName'] != value:
            print(f"  POTENTIAL BUG: {name} not preserved!")
            print(f"    Original: {repr(value)}")
            print(f"    After roundtrip: {repr(parsed['Properties']['DisplayName'])}")
            bug4 = True
    except Exception as e:
        print(f"  Error with {name}: {e}")
        bug4 = True

if not bug4:
    print("  OK: All special characters handled correctly")

# BUG TEST 5: Property reassignment after creation
print("\\nBUG TEST 5: Property modification after creation")
try:
    group = Group(
        title="Test",
        DisplayName="Original",
        IdentityStoreId="s-123"
    )
    
    # Modify the property
    group.DisplayName = "Modified"
    result1 = group.to_dict()
    
    # Try invalid type
    try:
        group.DisplayName = 12345
        result2 = group.to_dict()
        print("  POTENTIAL BUG: Type validation not enforced on reassignment!")
        print(f"    DisplayName is now: {result2['Properties']['DisplayName']}")
        bug5 = True
    except TypeError:
        print("  OK: Type validation enforced on reassignment")
        bug5 = False
        
except Exception as e:
    print(f"  Error: {e}")
    bug5 = False

# BUG TEST 6: _from_dict round-trip  
print("\\nBUG TEST 6: _from_dict round-trip property")
try:
    # Create original
    original = Group(
        title="Original",
        DisplayName="TestDisplay",
        IdentityStoreId="s-123",
        Description="TestDesc"
    )
    original_dict = original.to_dict()
    
    # Reconstruct from properties
    reconstructed = Group._from_dict(
        title="Reconstructed",
        **original_dict['Properties']
    )
    reconstructed_dict = reconstructed.to_dict()
    
    # Compare properties (not the whole dict since title differs)
    if original_dict['Properties'] != reconstructed_dict['Properties']:
        print("  POTENTIAL BUG: Round-trip through _from_dict failed!")
        print(f"    Original props: {original_dict['Properties']}")
        print(f"    Reconstructed props: {reconstructed_dict['Properties']}")
        bug6 = True
    else:
        print("  OK: Round-trip successful")
        bug6 = False
        
except Exception as e:
    print(f"  Error in round-trip: {e}")
    traceback.print_exc()
    bug6 = False

# BUG TEST 7: Title validation edge cases
print("\\nBUG TEST 7: Title validation edge cases")
try:
    # Test empty title
    try:
        group = Group(
            title="",
            DisplayName="Test",
            IdentityStoreId="s-123"
        )
        print("  POTENTIAL BUG: Empty title accepted!")
        bug7 = True
    except ValueError as e:
        if "alphanumeric" in str(e):
            print("  OK: Empty title rejected")
            bug7 = False
        else:
            print(f"  Unexpected error for empty title: {e}")
            bug7 = True
            
except Exception as e:
    print(f"  Error: {e}")
    bug7 = False

# BUG TEST 8: MemberId with dict initialization
print("\\nBUG TEST 8: GroupMembership._from_dict with nested MemberId")
try:
    # Create a dict representation
    membership_dict = {
        'GroupId': 'g-123',
        'IdentityStoreId': 's-123',
        'MemberId': {'UserId': 'u-456'}
    }
    
    # Try to create from dict
    membership = GroupMembership._from_dict(
        title="TestMembership",
        **membership_dict
    )
    result = membership.to_dict()
    
    # Check if MemberId was properly converted
    if isinstance(membership.MemberId, dict):
        print("  POTENTIAL BUG: MemberId not converted to MemberId object!")
        print(f"    MemberId type: {type(membership.MemberId)}")
        bug8 = True
    elif result['Properties']['MemberId']['UserId'] != 'u-456':
        print("  POTENTIAL BUG: MemberId data lost in conversion!")
        bug8 = True
    else:
        print("  OK: MemberId properly handled in _from_dict")
        bug8 = False
        
except Exception as e:
    print(f"  Error in _from_dict: {e}")
    traceback.print_exc()
    bug8 = False

# Summary
print("\\n" + "=" * 60)
print("BUG HUNT SUMMARY:")
bugs_found = []
if bug1: bugs_found.append("Dict accepted for MemberId instead of MemberId object")
if bug2: bugs_found.append("Empty string accepted for required DisplayName")
if bug3: bugs_found.append("None value included in JSON output")
if bug4: bugs_found.append("Special characters not properly handled")
if bug5: bugs_found.append("Type validation not enforced on property reassignment")
if bug6: bugs_found.append("Round-trip through _from_dict failed")
if bug7: bugs_found.append("Title validation issue")
if bug8: bugs_found.append("MemberId not properly handled in _from_dict")

if bugs_found:
    print(f"Found {len(bugs_found)} potential bug(s):")
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")
else:
    print("No bugs found - all tests passed!")
print("=" * 60)
""")