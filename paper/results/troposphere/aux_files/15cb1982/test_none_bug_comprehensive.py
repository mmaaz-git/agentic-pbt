import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cleanrooms as cleanrooms
from hypothesis import given, strategies as st
import pytest


def test_none_in_optional_properties_comprehensive():
    """Test None handling across different classes with optional properties."""
    
    bugs_found = []
    
    # Test 1: AnalysisParameter with optional DefaultValue
    try:
        obj = cleanrooms.AnalysisParameter(
            Name="test",
            Type="STRING",
            DefaultValue=None
        )
    except TypeError as e:
        bugs_found.append(("AnalysisParameter.DefaultValue", str(e)))
    
    # Test 2: AthenaTableReference with optional OutputLocation
    try:
        obj = cleanrooms.AthenaTableReference(
            DatabaseName="db",
            TableName="table",
            WorkGroup="wg",
            OutputLocation=None
        )
    except TypeError as e:
        bugs_found.append(("AthenaTableReference.OutputLocation", str(e)))
    
    # Test 3: AnalysisRuleAggregation with optional AdditionalAnalyses
    try:
        obj = cleanrooms.AnalysisRuleAggregation(
            AggregateColumns=[],
            DimensionColumns=[],
            JoinColumns=[],
            OutputConstraints=[],
            ScalarFunctions=[],
            AdditionalAnalyses=None
        )
    except TypeError as e:
        bugs_found.append(("AnalysisRuleAggregation.AdditionalAnalyses", str(e)))
    
    # Test 4: ConfiguredTable with optional Description
    try:
        obj = cleanrooms.ConfiguredTable(
            AllowedColumns=["col1"],
            AnalysisMethod="DIRECT_QUERY",
            Name="test",
            TableReference=cleanrooms.TableReference(
                Glue=cleanrooms.GlueTableReference(
                    DatabaseName="db",
                    TableName="table"
                )
            ),
            Description=None
        )
    except TypeError as e:
        bugs_found.append(("ConfiguredTable.Description", str(e)))
    
    # Test 5: ProtectedQueryS3OutputConfiguration with optional KeyPrefix
    try:
        obj = cleanrooms.ProtectedQueryS3OutputConfiguration(
            Bucket="bucket",
            ResultFormat="CSV",
            KeyPrefix=None
        )
    except TypeError as e:
        bugs_found.append(("ProtectedQueryS3OutputConfiguration.KeyPrefix", str(e)))
    
    # Test 6: Membership with optional PaymentConfiguration
    try:
        obj = cleanrooms.Membership(
            CollaborationIdentifier="collab-123",
            QueryLogStatus="ENABLED",
            PaymentConfiguration=None
        )
    except TypeError as e:
        bugs_found.append(("Membership.PaymentConfiguration", str(e)))
    
    return bugs_found


@given(
    # Generate random optional property scenarios
    class_name=st.sampled_from([
        "AnalysisParameter",
        "AthenaTableReference",
        "ConfiguredTable",
        "ProtectedQueryS3OutputConfiguration"
    ])
)
def test_none_bug_property_based(class_name):
    """Property-based test for None handling in optional properties."""
    
    test_cases = {
        "AnalysisParameter": {
            "required": {"Name": "test", "Type": "STRING"},
            "optional": "DefaultValue"
        },
        "AthenaTableReference": {
            "required": {"DatabaseName": "db", "TableName": "table", "WorkGroup": "wg"},
            "optional": "OutputLocation"
        },
        "ConfiguredTable": {
            "required": {
                "AllowedColumns": ["col1"],
                "AnalysisMethod": "DIRECT_QUERY",
                "Name": "test",
                "TableReference": cleanrooms.TableReference(
                    Glue=cleanrooms.GlueTableReference(
                        DatabaseName="db",
                        TableName="table"
                    )
                )
            },
            "optional": "Description"
        },
        "ProtectedQueryS3OutputConfiguration": {
            "required": {"Bucket": "bucket", "ResultFormat": "CSV"},
            "optional": "KeyPrefix"
        }
    }
    
    if class_name in test_cases:
        cls = getattr(cleanrooms, class_name)
        required = test_cases[class_name]["required"]
        optional_prop = test_cases[class_name]["optional"]
        
        # Test creating with None for optional property
        kwargs = {**required, optional_prop: None}
        
        with pytest.raises(TypeError, match=f"{optional_prop} is <class 'NoneType'>, expected"):
            obj = cls(**kwargs)
            obj.to_dict()


def test_workaround_for_none_bug():
    """Test if there's a workaround for the None bug."""
    
    print("Testing workarounds for None bug:")
    
    # Workaround 1: Don't set the property at all
    obj1 = cleanrooms.AnalysisParameter(Name="test", Type="STRING")
    dict1 = obj1.to_dict()
    print(f"1. Not setting property: {dict1}")
    assert "DefaultValue" not in dict1
    
    # Workaround 2: Delete property after creation (if possible)
    obj2 = cleanrooms.AnalysisParameter(Name="test", Type="STRING", DefaultValue="temp")
    try:
        del obj2.DefaultValue
        dict2 = obj2.to_dict()
        print(f"2. Deleting property: {dict2}")
    except Exception as e:
        print(f"2. Cannot delete property: {e}")
    
    # Workaround 3: Set to empty string (might not be semantically correct)
    obj3 = cleanrooms.AnalysisParameter(Name="test", Type="STRING", DefaultValue="")
    dict3 = obj3.to_dict()
    print(f"3. Setting to empty string: {dict3}")
    
    return True


def create_minimal_reproduction():
    """Create a minimal reproduction script for the bug."""
    
    script = '''#!/usr/bin/env python3
"""
Minimal reproduction of troposphere None handling bug.
This demonstrates that optional properties cannot be explicitly set to None.
"""

import troposphere.cleanrooms as cleanrooms

# This fails with TypeError
try:
    obj = cleanrooms.AnalysisParameter(
        Name="test",
        Type="STRING", 
        DefaultValue=None  # Optional property set to None
    )
    print("Success: Created object with None optional property")
except TypeError as e:
    print(f"BUG: {e}")

# This works - not setting the optional property
obj2 = cleanrooms.AnalysisParameter(
    Name="test",
    Type="STRING"
    # DefaultValue not set
)
print(f"Workaround works: {obj2.to_dict()}")
'''
    
    with open("reproduce_none_bug.py", "w") as f:
        f.write(script)
    
    print("Created reproduce_none_bug.py")
    return script


if __name__ == "__main__":
    print("=" * 60)
    print("COMPREHENSIVE NONE BUG TEST")
    print("=" * 60)
    
    bugs = test_none_in_optional_properties_comprehensive()
    
    if bugs:
        print(f"\nFound {len(bugs)} instances of the None bug:\n")
        for prop, error in bugs:
            print(f"  • {prop}")
            print(f"    Error: {error[:80]}...")
    
    print("\n" + "=" * 60)
    print("WORKAROUND TEST")
    print("=" * 60)
    test_workaround_for_none_bug()
    
    print("\n" + "=" * 60)
    print("CREATING MINIMAL REPRODUCTION")
    print("=" * 60)
    script = create_minimal_reproduction()
    print("\nMinimal reproduction script content:")
    print(script)