#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""
Property-based tests for troposphere using Hypothesis
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import re
from hypothesis import given, strategies as st, assume, settings
import troposphere
from troposphere import (
    Template, Parameter, Output, Ref, Tags, AWSObject, 
    BaseAWSObject, Base64, Join, Sub, Select, GetAtt,
    FindInMap, validators
)
from troposphere.ec2 import Instance, SecurityGroup


# Strategy for valid alphanumeric CloudFormation resource names
valid_cfn_names = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=255
).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x))

# Strategy for invalid names (non-alphanumeric)
invalid_cfn_names = st.text(min_size=1, max_size=100).filter(
    lambda x: not re.match(r'^[a-zA-Z0-9]+$', x) and x != ""
)


# Property 1: Title validation - titles must be alphanumeric
@given(valid_cfn_names)
def test_valid_titles_accepted(title):
    """Valid alphanumeric titles should be accepted"""
    try:
        param = Parameter(title, Type="String")
        assert param.title == title
        param.validate_title()  # Should not raise
    except ValueError as e:
        if "alphanumeric" in str(e):
            raise


@given(invalid_cfn_names)
def test_invalid_titles_rejected(title):
    """Non-alphanumeric titles should be rejected"""
    param = Parameter("ValidName", Type="String")  # Create with valid name first
    param.title = title  # Then set invalid title
    try:
        param.validate_title()
        assert False, f"Title '{title}' should have been rejected"
    except ValueError as e:
        assert "alphanumeric" in str(e)


# Property 2: Template limits enforcement
@given(st.integers(min_value=201, max_value=1000))
def test_template_parameter_limit(num_params):
    """Template should reject more than MAX_PARAMETERS parameters"""
    template = Template()
    
    # Add parameters up to the limit
    for i in range(troposphere.MAX_PARAMETERS):
        param = Parameter(f"Param{i}", Type="String")
        template.add_parameter(param)
    
    # Adding one more should fail
    try:
        extra_param = Parameter(f"Param{troposphere.MAX_PARAMETERS}", Type="String")
        template.add_parameter(extra_param)
        assert False, "Should have raised error for exceeding parameter limit"
    except ValueError as e:
        assert "Maximum parameters" in str(e)


@given(st.integers(min_value=201, max_value=1000))
def test_template_output_limit(num_outputs):
    """Template should reject more than MAX_OUTPUTS outputs"""
    template = Template()
    
    # Add outputs up to the limit
    for i in range(troposphere.MAX_OUTPUTS):
        output = Output(f"Output{i}", Value="test")
        template.add_output(output)
    
    # Adding one more should fail
    try:
        extra_output = Output(f"Output{troposphere.MAX_OUTPUTS}", Value="test")
        template.add_output(extra_output)
        assert False, "Should have raised error for exceeding output limit"
    except ValueError as e:
        assert "Maximum outputs" in str(e)


# Property 3: JSON round-trip for Parameters
@given(
    title=valid_cfn_names,
    param_type=st.sampled_from(["String", "Number", "List<Number>", "CommaDelimitedList"]),
    description=st.text(max_size=100)
)
def test_parameter_json_roundtrip(title, param_type, description):
    """Parameters should survive JSON serialization round-trip"""
    param = Parameter(
        title,
        Type=param_type,
        Description=description if description else None
    )
    
    # Convert to dict then JSON
    param_dict = param.to_dict()
    json_str = json.dumps(param_dict)
    
    # Parse back
    parsed = json.loads(json_str)
    
    # Verify key properties preserved
    assert parsed["Type"] == param_type
    if description:
        assert parsed.get("Description") == description


# Property 4: Ref equality
@given(
    name1=valid_cfn_names,
    name2=valid_cfn_names
)
def test_ref_equality(name1, name2):
    """Refs to the same resource should be equal, different resources should not"""
    ref1a = Ref(name1)
    ref1b = Ref(name1)
    ref2 = Ref(name2)
    
    # Same resource refs should be equal
    assert ref1a == ref1b
    assert hash(ref1a) == hash(ref1b)
    
    # Different resource refs should not be equal (unless names happen to be same)
    if name1 != name2:
        assert ref1a != ref2
        assert hash(ref1a) != hash(ref2)


# Property 5: Tags concatenation preserves all tags
@given(
    tags1=st.dictionaries(
        st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
        st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=10
    ),
    tags2=st.dictionaries(
        st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
        st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=10
    )
)
def test_tags_concatenation(tags1, tags2):
    """Tags concatenation with + should preserve all tags"""
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    
    combined = t1 + t2
    combined_dict = combined.to_dict()
    
    # All tags from t1 should be in combined
    t1_dict = t1.to_dict()
    for tag in t1_dict:
        assert tag in combined_dict
    
    # All tags from t2 should be in combined
    t2_dict = t2.to_dict()
    for tag in t2_dict:
        assert tag in combined_dict
    
    # Total count should be sum
    assert len(combined_dict) == len(t1_dict) + len(t2_dict)


# Property 6: Template to_dict and to_json consistency
@given(
    description=st.text(max_size=100),
    num_params=st.integers(min_value=0, max_value=5)
)
def test_template_serialization_consistency(description, num_params):
    """Template to_dict and to_json should be consistent"""
    template = Template(Description=description if description else None)
    
    # Add some parameters
    for i in range(num_params):
        param = Parameter(f"Param{i}", Type="String")
        template.add_parameter(param)
    
    # Get dict and json representations
    template_dict = template.to_dict()
    template_json = template.to_json()
    
    # Parse JSON back to dict
    parsed_dict = json.loads(template_json)
    
    # Should be equivalent
    assert template_dict == parsed_dict


# Property 7: Parameter default type validation
@given(
    param_type=st.sampled_from(["String", "Number"]),
    default_value=st.one_of(
        st.text(max_size=50),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_parameter_default_type_checking(param_type, default_value):
    """Parameter default values should match their declared type"""
    if param_type == "String":
        # String type should accept string defaults
        if isinstance(default_value, str):
            param = Parameter("Test", Type=param_type, Default=default_value)
            param.validate()  # Should not raise
        else:
            try:
                param = Parameter("Test", Type=param_type, Default=default_value)
                param.validate()
                assert False, "Should have rejected non-string default for String type"
            except (ValueError, TypeError) as e:
                assert "type mismatch" in str(e) or "String" in str(e)
    
    elif param_type == "Number":
        # Number type should accept numeric defaults
        if isinstance(default_value, (int, float)) and not isinstance(default_value, bool):
            param = Parameter("Test", Type=param_type, Default=default_value)
            param.validate()  # Should not raise
        elif isinstance(default_value, str):
            # String representation of number might be accepted
            try:
                float(default_value)
                param = Parameter("Test", Type=param_type, Default=default_value)
                param.validate()
            except ValueError:
                # Not a valid number string
                try:
                    param = Parameter("Test", Type=param_type, Default=default_value)
                    param.validate()
                    assert False, "Should have rejected non-numeric default"
                except (ValueError, TypeError):
                    pass  # Expected


# Property 8: Base64 encoding helper
@given(st.text())
def test_base64_helper_preserves_data(data):
    """Base64 helper should preserve input data in Fn::Base64 structure"""
    b64 = Base64(data)
    result = b64.to_dict()
    assert result == {"Fn::Base64": data}


# Property 9: Join helper with valid delimiters
@given(
    delimiter=st.text(min_size=1, max_size=10),
    values=st.lists(st.text(max_size=50), min_size=1, max_size=10)
)
def test_join_helper(delimiter, values):
    """Join helper should create correct CloudFormation Join function"""
    join = Join(delimiter, values)
    result = join.to_dict()
    assert result == {"Fn::Join": [delimiter, values]}


# Property 10: Template duplicate resource detection
@given(
    resource_name=valid_cfn_names,
    num_attempts=st.integers(min_value=2, max_value=5)
)
def test_template_duplicate_resource_detection(resource_name, num_attempts):
    """Template should detect and reject duplicate resource names"""
    template = Template()
    
    # First resource should succeed
    resource1 = Parameter(resource_name, Type="String")
    template.add_parameter(resource1)
    
    # Subsequent attempts with same name should fail
    for i in range(num_attempts - 1):
        resource2 = Parameter(resource_name, Type="String")
        try:
            template.add_parameter(resource2)
            assert False, f"Should have rejected duplicate resource name: {resource_name}"
        except ValueError as e:
            assert "duplicate" in str(e).lower()


# Property 11: Parameter title length limit
@given(st.text(min_size=256, max_size=500))
def test_parameter_title_length_limit(long_title):
    """Parameter titles longer than 255 characters should be rejected"""
    # Ensure it's actually longer than the limit
    assume(len(long_title) > troposphere.PARAMETER_TITLE_MAX)
    
    try:
        param = Parameter(long_title, Type="String")
        param.validate_title()
        assert False, "Should have rejected title longer than 255 characters"
    except ValueError as e:
        assert "longer than" in str(e) or "255" in str(e)


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])