import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cleanrooms as cleanrooms
import pytest


def test_none_optional_property_bug():
    """Demonstrate bug: Setting optional property to None raises TypeError."""
    # This should not raise an error - DefaultValue is optional
    # But it raises: TypeError: DefaultValue is <class 'NoneType'>, expected <class 'str'>
    
    try:
        obj = cleanrooms.AnalysisParameter(
            Name="test",
            Type="STRING",
            DefaultValue=None  # Explicitly setting optional property to None
        )
        print("No error - object created successfully")
        d = obj.to_dict()
        print(f"Dict representation: {d}")
    except TypeError as e:
        print(f"BUG FOUND: {e}")
        return True
    
    return False


def test_from_dict_missing_required_field_bug():
    """Demonstrate bug: from_dict doesn't validate required fields."""
    # S3Location requires both Bucket and Key
    # But from_dict doesn't raise an error when Key is missing
    
    try:
        # Create from dict with missing required field
        obj = cleanrooms.S3Location._from_dict(Bucket="test")  # Missing required Key
        print("No error - object created without required field")
        
        # Now try to convert to dict - this should fail
        try:
            d = obj.to_dict()
            print(f"BUG: to_dict() succeeded without required field: {d}")
            return True  # This is a bug - required field was missing
        except ValueError as e:
            print(f"to_dict() correctly failed: {e}")
            return False  # Expected behavior
            
    except (ValueError, KeyError, AttributeError) as e:
        print(f"from_dict correctly failed: {e}")
        return False


def test_from_dict_unknown_field():
    """Test if from_dict handles unknown fields correctly."""
    try:
        obj = cleanrooms.S3Location._from_dict(
            Bucket="test",
            Key="test",
            UnknownField="value"  # This field doesn't exist
        )
        print("BUG: from_dict accepted unknown field")
        return True
    except AttributeError as e:
        print(f"Correctly rejected unknown field: {e}")
        return False


def test_none_handling_in_different_contexts():
    """Test how None is handled in different contexts."""
    
    print("\n1. Testing None in optional property at creation:")
    try:
        obj1 = cleanrooms.AnalysisParameter(
            Name="test",
            Type="STRING",
            DefaultValue=None
        )
        print("  Created with DefaultValue=None")
    except TypeError as e:
        print(f"  Failed with: {e}")
    
    print("\n2. Testing without setting optional property:")
    try:
        obj2 = cleanrooms.AnalysisParameter(
            Name="test",
            Type="STRING"
            # DefaultValue not set at all
        )
        print(f"  Created without DefaultValue: {obj2.to_dict()}")
    except Exception as e:
        print(f"  Failed with: {e}")
    
    print("\n3. Testing setting None after creation:")
    try:
        obj3 = cleanrooms.AnalysisParameter(
            Name="test",
            Type="STRING"
        )
        obj3.DefaultValue = None
        print(f"  Set DefaultValue=None after creation")
        print(f"  to_dict: {obj3.to_dict()}")
    except Exception as e:
        print(f"  Failed with: {e}")


def test_from_dict_roundtrip_with_missing_optional():
    """Test if from_dict handles missing optional fields correctly."""
    
    # Create object without optional field
    obj1 = cleanrooms.AnalysisParameter(Name="test", Type="STRING")
    dict1 = obj1.to_dict()
    print(f"Original dict (no DefaultValue): {dict1}")
    
    # Create from dict
    obj2 = cleanrooms.AnalysisParameter._from_dict(**dict1)
    dict2 = obj2.to_dict()
    print(f"Roundtrip dict: {dict2}")
    
    assert dict1 == dict2, "Roundtrip failed"
    
    # Now test with optional field set
    obj3 = cleanrooms.AnalysisParameter(Name="test", Type="STRING", DefaultValue="default")
    dict3 = obj3.to_dict()
    print(f"Dict with DefaultValue: {dict3}")
    
    obj4 = cleanrooms.AnalysisParameter._from_dict(**dict3)
    dict4 = obj4.to_dict()
    print(f"Roundtrip dict with DefaultValue: {dict4}")
    
    assert dict3 == dict4, "Roundtrip with optional field failed"


if __name__ == "__main__":
    print("=" * 60)
    print("BUG INVESTIGATION REPORT")
    print("=" * 60)
    
    print("\nTest 1: None in optional property")
    print("-" * 40)
    bug1 = test_none_optional_property_bug()
    
    print("\nTest 2: from_dict with missing required field")
    print("-" * 40)
    bug2 = test_from_dict_missing_required_field_bug()
    
    print("\nTest 3: from_dict with unknown field")
    print("-" * 40)
    bug3 = test_from_dict_unknown_field()
    
    print("\nTest 4: None handling investigation")
    print("-" * 40)
    test_none_handling_in_different_contexts()
    
    print("\nTest 5: from_dict roundtrip")
    print("-" * 40)
    test_from_dict_roundtrip_with_missing_optional()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    bugs_found = []
    if bug1:
        bugs_found.append("Setting optional property to None raises TypeError")
    if bug2:
        bugs_found.append("from_dict doesn't validate required fields early")
    if bug3:
        bugs_found.append("from_dict accepts unknown fields")
    
    if bugs_found:
        print(f"Found {len(bugs_found)} bug(s):")
        for i, bug in enumerate(bugs_found, 1):
            print(f"  {i}. {bug}")
    else:
        print("No clear bugs found in these tests")