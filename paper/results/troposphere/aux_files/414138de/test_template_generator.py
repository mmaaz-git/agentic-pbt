"""Property-based tests for troposphere.template_generator.TemplateGenerator"""

import troposphere.template_generator as tg
from hypothesis import given, strategies as st, assume, settings
import json


# Strategy for CloudFormation resource types (only valid AWS types)
aws_resource_types = st.sampled_from([
    "AWS::S3::Bucket",
    "AWS::EC2::Instance", 
    "AWS::Lambda::Function",
    "AWS::DynamoDB::Table",
    "AWS::IAM::Role",
    "AWS::SNS::Topic",
    "AWS::SQS::Queue",
    "AWS::EC2::SecurityGroup",
    "AWS::RDS::DBInstance",
    "AWS::CloudWatch::Alarm"
])

# Strategy for simple property values (avoiding complex nested structures initially)
simple_values = st.one_of(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    st.integers(min_value=0, max_value=1000),
    st.booleans()
)

# Strategy for CloudFormation intrinsic functions
intrinsic_functions = st.one_of(
    st.dictionaries(st.just("Ref"), st.text(min_size=1, max_size=50)),
    st.dictionaries(st.just("Fn::GetAtt"), 
                   st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=2))
)

# Strategy for resource properties
resource_properties = st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.one_of(simple_values, intrinsic_functions),
    min_size=0,
    max_size=5
)

# Strategy for a single CloudFormation resource
cf_resource = st.fixed_dictionaries({
    "Type": aws_resource_types,
    "Properties": resource_properties
})

# Strategy for CloudFormation parameters
cf_parameter = st.fixed_dictionaries({
    "Type": st.sampled_from(["String", "Number", "List<Number>", "CommaDelimitedList"]),
    "Description": st.text(min_size=1, max_size=100)
})

# Strategy for CloudFormation outputs
cf_output = st.fixed_dictionaries({
    "Value": st.one_of(simple_values, intrinsic_functions),
    "Description": st.text(min_size=0, max_size=100)
})

# Strategy for complete CloudFormation templates
cf_templates = st.fixed_dictionaries({
    "AWSTemplateFormatVersion": st.just("2010-09-09"),
    "Resources": st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
        cf_resource,
        min_size=1,
        max_size=5
    )
}, optional={
    "Description": st.text(min_size=1, max_size=200),
    "Parameters": st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
        cf_parameter,
        min_size=0,
        max_size=3
    ),
    "Outputs": st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
        cf_output,
        min_size=0,
        max_size=3
    )
})


@given(cf_templates)
@settings(max_examples=100)
def test_round_trip_preserves_structure(cf_template):
    """
    Property: Converting CloudFormation to Troposphere and back preserves structure
    """
    # Convert to Troposphere
    tg_template = tg.TemplateGenerator(cf_template)
    
    # Convert back to dict
    result = tg_template.to_dict()
    
    # Check that all top-level keys are preserved
    assert set(cf_template.keys()) == set(result.keys()), \
        f"Keys mismatch: {set(cf_template.keys())} != {set(result.keys())}"
    
    # Check resource count is preserved
    if "Resources" in cf_template:
        assert len(cf_template["Resources"]) == len(result["Resources"]), \
            f"Resource count mismatch: {len(cf_template['Resources'])} != {len(result['Resources'])}"
        
        # Check all resource names are preserved
        assert set(cf_template["Resources"].keys()) == set(result["Resources"].keys()), \
            "Resource names not preserved"
    
    # Check parameter count is preserved
    if "Parameters" in cf_template:
        assert len(cf_template["Parameters"]) == len(result["Parameters"]), \
            f"Parameter count mismatch"
        
        # Check all parameter names are preserved
        assert set(cf_template["Parameters"].keys()) == set(result["Parameters"].keys()), \
            "Parameter names not preserved"
    
    # Check output count is preserved
    if "Outputs" in cf_template:
        assert len(cf_template["Outputs"]) == len(result["Outputs"]), \
            f"Output count mismatch"
        
        # Check all output names are preserved
        assert set(cf_template["Outputs"].keys()) == set(result["Outputs"].keys()), \
            "Output names not preserved"
    
    # Check description is preserved
    if "Description" in cf_template:
        assert result["Description"] == cf_template["Description"], \
            "Description not preserved"


@given(st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.fixed_dictionaries({  # Resource without Type field
        "Properties": resource_properties
    }),
    min_size=1,
    max_size=3
))
def test_missing_type_raises_error(resources_without_type):
    """
    Property: Resources without Type field should raise ResourceTypeNotDefined
    """
    cf_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": resources_without_type
    }
    
    # Should raise ResourceTypeNotDefined
    try:
        tg.TemplateGenerator(cf_template)
        assert False, "Should have raised ResourceTypeNotDefined"
    except tg.ResourceTypeNotDefined as e:
        # Expected - check the error message contains the resource name
        resource_name = list(resources_without_type.keys())[0]
        assert resource_name in str(e), f"Error message should contain resource name {resource_name}"


@given(st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.fixed_dictionaries({
        "Type": st.text(min_size=10, max_size=100).filter(
            lambda x: not x.startswith("AWS::") and not x.startswith("Custom::")
        ),
        "Properties": resource_properties
    }),
    min_size=1,
    max_size=3
))
def test_unknown_resource_type_raises_error(resources_with_unknown_type):
    """
    Property: Unknown resource types should raise ResourceTypeNotFound
    """
    cf_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": resources_with_unknown_type
    }
    
    # Should raise ResourceTypeNotFound
    try:
        tg.TemplateGenerator(cf_template)
        assert False, "Should have raised ResourceTypeNotFound"
    except tg.ResourceTypeNotFound:
        # Expected
        pass


@given(cf_templates)
@settings(max_examples=100)
def test_intrinsic_functions_preserved(cf_template):
    """
    Property: CloudFormation intrinsic functions (Ref, Fn::GetAtt, etc.) are preserved
    """
    # Convert to Troposphere
    tg_template = tg.TemplateGenerator(cf_template)
    
    # Convert back to dict
    result = tg_template.to_dict()
    
    # Check if any Ref functions in original are preserved
    original_json = json.dumps(cf_template)
    result_json = json.dumps(result)
    
    # Count Ref occurrences (simple check)
    if '"Ref"' in original_json:
        assert '"Ref"' in result_json, "Ref functions not preserved"
        
    # Count Fn::GetAtt occurrences
    if '"Fn::GetAtt"' in original_json:
        assert '"Fn::GetAtt"' in result_json, "Fn::GetAtt functions not preserved"


@given(cf_templates)
@settings(max_examples=50)
def test_double_conversion_idempotent(cf_template):
    """
    Property: Converting twice should be idempotent (second conversion produces same result)
    """
    # First conversion
    tg_template1 = tg.TemplateGenerator(cf_template)
    result1 = tg_template1.to_dict()
    
    # Second conversion (convert the result back)
    tg_template2 = tg.TemplateGenerator(result1)
    result2 = tg_template2.to_dict()
    
    # Results should be identical
    assert result1 == result2, "Double conversion is not idempotent"


# Strategy for templates with metadata and policies
templates_with_metadata = st.fixed_dictionaries({
    "AWSTemplateFormatVersion": st.just("2010-09-09"),
    "Resources": st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
        st.fixed_dictionaries({
            "Type": aws_resource_types,
            "Properties": resource_properties,
            "Metadata": st.dictionaries(
                st.text(min_size=1, max_size=20),
                simple_values,
                min_size=1,
                max_size=3
            ),
            "DependsOn": st.one_of(
                st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
                st.lists(st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()), 
                        min_size=1, max_size=3)
            ),
            "DeletionPolicy": st.sampled_from(["Delete", "Retain", "Snapshot"]),
            "Condition": st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum())
        }, optional=["Metadata", "DependsOn", "DeletionPolicy", "Condition"]),
        min_size=1,
        max_size=3
    )
})


@given(templates_with_metadata)
@settings(max_examples=50)
def test_metadata_and_policies_preserved(cf_template):
    """
    Property: Resource metadata, DependsOn, DeletionPolicy, and Condition are preserved
    """
    # Convert to Troposphere
    tg_template = tg.TemplateGenerator(cf_template)
    
    # Convert back to dict
    result = tg_template.to_dict()
    
    # Check each resource
    for resource_name, resource_def in cf_template["Resources"].items():
        result_resource = result["Resources"][resource_name]
        
        # Check metadata preserved
        if "Metadata" in resource_def:
            assert "Metadata" in result_resource, f"Metadata not preserved for {resource_name}"
            assert result_resource["Metadata"] == resource_def["Metadata"], \
                f"Metadata content differs for {resource_name}"
        
        # Check DependsOn preserved
        if "DependsOn" in resource_def:
            assert "DependsOn" in result_resource, f"DependsOn not preserved for {resource_name}"
            assert result_resource["DependsOn"] == resource_def["DependsOn"], \
                f"DependsOn differs for {resource_name}"
        
        # Check DeletionPolicy preserved
        if "DeletionPolicy" in resource_def:
            assert "DeletionPolicy" in result_resource, f"DeletionPolicy not preserved for {resource_name}"
            assert result_resource["DeletionPolicy"] == resource_def["DeletionPolicy"], \
                f"DeletionPolicy differs for {resource_name}"
        
        # Check Condition preserved
        if "Condition" in resource_def:
            assert "Condition" in result_resource, f"Condition not preserved for {resource_name}"
            assert result_resource["Condition"] == resource_def["Condition"], \
                f"Condition differs for {resource_name}"