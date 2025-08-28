#!/usr/bin/env python3
"""More comprehensive edge case testing for troposphere.networkmanager"""

import sys
import traceback
import json

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import troposphere.networkmanager as nm
from troposphere.validators import boolean, double, integer

print("Running edge case tests for troposphere.networkmanager...")
print("=" * 60)

# Test 1: Empty string handling in validators
print("\nTest 1: Empty string handling in validators")
try:
    # Test empty string with integer validator
    try:
        result = integer("")
        print(f"✗ Failed: integer('') returned {result}, should raise ValueError")
    except ValueError:
        print("✓ integer('') correctly raises ValueError")
    
    # Test empty string with double validator
    try:
        result = double("")
        print(f"✗ Failed: double('') returned {result}, should raise ValueError")
    except ValueError:
        print("✓ double('') correctly raises ValueError")
    
    # Test empty string with boolean validator
    try:
        result = boolean("")
        print(f"✗ Failed: boolean('') returned {result}, should raise ValueError")
    except ValueError:
        print("✓ boolean('') correctly raises ValueError")
        
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    traceback.print_exc()

# Test 2: Special numeric values
print("\nTest 2: Special numeric values in validators")
try:
    # Test negative zero
    assert integer(-0) == -0
    assert integer("-0") == "-0"
    print("✓ integer handles negative zero")
    
    # Test very large numbers
    large_num = 10**100
    assert integer(large_num) == large_num
    assert integer(str(large_num)) == str(large_num)
    print("✓ integer handles very large numbers")
    
    # Test scientific notation with double
    assert double("1e10") == "1e10"
    assert double(1e10) == 1e10
    print("✓ double handles scientific notation")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 3: Property validation with None values
print("\nTest 3: Property handling of None values")
try:
    # Test optional properties with None
    location = nm.Location()
    dict_repr = location.to_dict()
    print(f"✓ Location with no properties: {dict_repr}")
    
    # Test setting None explicitly
    location = nm.Location(Address=None)
    dict_repr = location.to_dict()
    assert "Address" not in dict_repr or dict_repr["Address"] is None
    print("✓ Setting None on optional property works")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 4: Testing required vs optional properties  
print("\nTest 4: Required property enforcement")
try:
    # Try creating ConnectAttachment without required properties
    try:
        attachment = nm.ConnectAttachment("Test")
        # Try to convert to dict without required properties
        dict_repr = attachment.to_dict()
        print(f"✗ Failed: ConnectAttachment.to_dict() succeeded without required properties")
    except Exception as e:
        print(f"✓ ConnectAttachment.to_dict() correctly fails without required properties: {type(e).__name__}")
    
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    traceback.print_exc()

# Test 5: Tags handling
print("\nTest 5: Tags property handling")
try:
    from troposphere import Tags
    
    # Test with empty tags
    device = nm.Device("TestDevice", GlobalNetworkId="test-network")
    device.Tags = Tags()
    dict_repr = device.to_dict()
    print(f"✓ Empty Tags handled: {dict_repr.get('Properties', {}).get('Tags')}")
    
    # Test with actual tags
    device.Tags = Tags(Environment="test", Owner="admin")
    dict_repr = device.to_dict()
    tags = dict_repr.get('Properties', {}).get('Tags', [])
    print(f"✓ Tags with values: {tags}")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 6: List property handling
print("\nTest 6: List property handling")
try:
    # Test EdgeLocations list property
    attachment = nm.DirectConnectGatewayAttachment(
        "TestDCG",
        CoreNetworkId="core-123",
        DirectConnectGatewayArn="arn:aws:directconnect",
        EdgeLocations=["us-east-1", "us-west-2"]
    )
    dict_repr = attachment.to_dict()
    assert dict_repr["Properties"]["EdgeLocations"] == ["us-east-1", "us-west-2"]
    print("✓ List properties handled correctly")
    
    # Test empty list
    attachment.EdgeLocations = []
    dict_repr = attachment.to_dict()
    assert dict_repr["Properties"]["EdgeLocations"] == []
    print("✓ Empty list handled correctly")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 7: Unicode and special characters
print("\nTest 7: Unicode and special character handling")
try:
    # Test unicode in string properties
    location = nm.Location(
        Address="123 Main St 🏠",
        Latitude="40.7128° N",
        Longitude="74.0060° W"
    )
    dict_repr = location.to_dict()
    assert dict_repr["Address"] == "123 Main St 🏠"
    print("✓ Unicode characters preserved")
    
    # Test special characters in identifiers
    site = nm.Site(
        "TestSite",
        GlobalNetworkId="global-123",
        Description="Test & Development <Site>"
    )
    dict_repr = site.to_dict()
    assert dict_repr["Properties"]["Description"] == "Test & Development <Site>"
    print("✓ Special characters in descriptions preserved")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 8: JSON serialization edge cases
print("\nTest 8: JSON serialization edge cases")
try:
    @given(
        description=st.text(min_size=0, max_size=500)
    )
    @settings(max_examples=100)
    def test_json_serialization(description):
        network = nm.GlobalNetwork("TestNetwork")
        if description:
            network.Description = description
        
        # Should be able to serialize to JSON
        json_str = network.to_json()
        parsed = json.loads(json_str)
        
        # And back to dict should match
        dict_repr = network.to_dict()
        if "Properties" in dict_repr and "Description" in dict_repr["Properties"]:
            assert parsed["Properties"]["Description"] == description
    
    test_json_serialization()
    print("✓ JSON serialization handles all text inputs")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 9: Property type coercion edge cases
print("\nTest 9: Property type coercion edge cases")
try:
    # Test string representations of booleans
    options = nm.VpcOptions()
    
    # These should work based on boolean validator
    options.ApplianceModeSupport = "true"
    dict_repr = options.to_dict()
    assert dict_repr["ApplianceModeSupport"] is True
    print("✓ String 'true' coerced to boolean True")
    
    options.Ipv6Support = 0
    dict_repr = options.to_dict()
    assert dict_repr["Ipv6Support"] is False
    print("✓ Integer 0 coerced to boolean False")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 10: Deeply nested property structures
print("\nTest 10: Nested property structures")
try:
    # Test nested properties
    attachment = nm.VpcAttachment(
        "TestVpc",
        CoreNetworkId="core-123",
        VpcArn="arn:aws:ec2:region:account:vpc/vpc-123",
        SubnetArns=["arn:aws:ec2:region:account:subnet/subnet-1"],
        Options=nm.VpcOptions(
            ApplianceModeSupport=True,
            Ipv6Support=False
        ),
        ProposedSegmentChange=nm.ProposedSegmentChange(
            SegmentName="test-segment",
            AttachmentPolicyRuleNumber=100
        )
    )
    
    dict_repr = attachment.to_dict()
    
    # Verify nested structure
    assert dict_repr["Properties"]["Options"]["ApplianceModeSupport"] is True
    assert dict_repr["Properties"]["ProposedSegmentChange"]["SegmentName"] == "test-segment"
    print("✓ Nested properties serialize correctly")
    
    # Test round-trip with nested properties
    reconstructed = nm.VpcAttachment._from_dict(
        "TestVpc",
        **dict_repr["Properties"]
    )
    assert reconstructed.to_dict() == dict_repr
    print("✓ Nested properties survive round-trip")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Edge case testing complete!")