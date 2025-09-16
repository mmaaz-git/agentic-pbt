#!/usr/bin/env python3
"""Property-based tests for troposphere library."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re
from hypothesis import given, strategies as st, assume, settings
import troposphere
from troposphere import (
    Template, Tags, Parameter, Output, AWSObject,
    Join, Split, Base64, Ref, encode_to_dict, depends_on_helper
)


# Strategy for valid CloudFormation resource names (alphanumeric only)
valid_cf_names = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=100
).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x))


# Test 1: Tags concatenation is associative
@given(
    tags1=st.dictionaries(st.text(min_size=1), st.text(), min_size=0, max_size=10),
    tags2=st.dictionaries(st.text(min_size=1), st.text(), min_size=0, max_size=10),
    tags3=st.dictionaries(st.text(min_size=1), st.text(), min_size=0, max_size=10)
)
def test_tags_concatenation_associative(tags1, tags2, tags3):
    """Test that Tags concatenation is associative: (a + b) + c == a + (b + c)"""
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    t3 = Tags(**tags3)
    
    # (t1 + t2) + t3
    left_assoc = (t1 + t2) + t3
    
    # t1 + (t2 + t3)
    right_assoc = t1 + (t2 + t3)
    
    # The resulting tag lists should be equal
    assert left_assoc.to_dict() == right_assoc.to_dict()


# Test 2: Template enforces resource limits
@given(
    num_resources=st.integers(min_value=0, max_value=600)
)
def test_template_resource_limits(num_resources):
    """Test that Template enforces MAX_RESOURCES limit"""
    template = Template()
    
    # Try to add resources up to the limit
    for i in range(num_resources):
        try:
            # Create a minimal AWS resource
            resource = AWSObject(f"Resource{i}")
            resource.resource_type = "AWS::CloudFormation::WaitConditionHandle"
            template.add_resource(resource)
        except ValueError as e:
            # Should only fail if we exceed MAX_RESOURCES
            assert num_resources > troposphere.MAX_RESOURCES
            assert "Maximum number of resources" in str(e)
            return
    
    # If we got here, we should be within the limit
    assert num_resources <= troposphere.MAX_RESOURCES


# Test 3: Parameter title validation
@given(title=st.text())
def test_parameter_title_validation(title):
    """Test that Parameter validates title according to rules"""
    try:
        param = Parameter(title, Type="String")
        # If successful, title should be alphanumeric and <= 255 chars
        assert re.match(r'^[a-zA-Z0-9]+$', title)
        assert len(title) <= troposphere.PARAMETER_TITLE_MAX
    except ValueError as e:
        # Should fail if not alphanumeric or too long
        if "not alphanumeric" in str(e):
            assert not re.match(r'^[a-zA-Z0-9]+$', title)
        elif "can be no longer than" in str(e):
            assert len(title) > troposphere.PARAMETER_TITLE_MAX


# Test 4: encode_to_dict is idempotent for dicts
@given(
    data=st.dictionaries(
        st.text(min_size=1),
        st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none()
        ),
        min_size=0,
        max_size=10
    )
)
def test_encode_to_dict_idempotent(data):
    """Test that encode_to_dict is idempotent: f(f(x)) == f(x)"""
    encoded_once = encode_to_dict(data)
    encoded_twice = encode_to_dict(encoded_once)
    assert encoded_once == encoded_twice


# Test 5: Join requires string delimiter
@given(
    delimiter=st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False),
        st.booleans(),
        st.none(),
        st.lists(st.text())
    ),
    values=st.lists(st.text(), min_size=1, max_size=10)
)
def test_join_delimiter_validation(delimiter, values):
    """Test that Join validates delimiter is a string"""
    try:
        j = Join(delimiter, values)
        # If successful, delimiter should be a string
        assert isinstance(delimiter, str)
    except ValueError as e:
        # Should fail if delimiter is not a string
        assert "Delimiter must be a String" in str(e)
        assert not isinstance(delimiter, str)


# Test 6: Split has same delimiter validation as Join
@given(
    delimiter=st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False),
        st.booleans(),
        st.none()
    ),
    value=st.text()
)
def test_split_delimiter_validation(delimiter, value):
    """Test that Split validates delimiter is a string (same as Join)"""
    try:
        s = Split(delimiter, value)
        # If successful, delimiter should be a string
        assert isinstance(delimiter, str)
    except ValueError as e:
        # Should fail if delimiter is not a string
        assert "Delimiter must be a String" in str(e)
        assert not isinstance(delimiter, str)


# Test 7: Parameter Default type validation for String type
@given(
    default_value=st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False),
        st.booleans(),
        st.none()
    )
)
def test_parameter_string_default_validation(default_value):
    """Test that Parameter validates Default value matches String type"""
    assume(default_value is not None)  # None means no default
    
    try:
        param = Parameter("TestParam", Type="String", Default=default_value)
        param.validate()
        # If successful, default should be a string
        assert isinstance(default_value, str)
    except (ValueError, TypeError) as e:
        # Should fail if default is not a string
        if "type mismatch" in str(e):
            assert not isinstance(default_value, str)


# Test 8: Parameter Default type validation for Number type
@given(
    default_value=st.one_of(
        st.text(min_size=1),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans()
    )
)
def test_parameter_number_default_validation(default_value):
    """Test that Parameter validates Default value for Number type"""
    try:
        param = Parameter("TestParam", Type="Number", Default=default_value)
        param.validate()
        # If successful, default should be numeric or convertible to numeric
        if isinstance(default_value, str):
            # Try to convert to float to verify it's numeric
            try:
                float(default_value)
            except ValueError:
                # String is not numeric, but validation passed - this would be a bug
                assert False, f"Non-numeric string {default_value!r} passed Number validation"
        else:
            assert isinstance(default_value, (int, float))
    except (ValueError, TypeError) as e:
        # Type validation failed - this is expected for non-numeric values
        pass


# Test 9: Template parameter limits
@given(num_params=st.integers(min_value=0, max_value=250))
def test_template_parameter_limits(num_params):
    """Test that Template enforces MAX_PARAMETERS limit"""
    template = Template()
    
    for i in range(num_params):
        try:
            param = Parameter(f"Param{i}", Type="String")
            template.add_parameter(param)
        except ValueError as e:
            # Should only fail if we exceed MAX_PARAMETERS
            assert num_params > troposphere.MAX_PARAMETERS
            assert "Maximum parameters" in str(e)
            return
    
    # If we got here, we should be within the limit
    assert num_params <= troposphere.MAX_PARAMETERS


# Test 10: Template output limits
@given(num_outputs=st.integers(min_value=0, max_value=250))
def test_template_output_limits(num_outputs):
    """Test that Template enforces MAX_OUTPUTS limit"""
    template = Template()
    
    for i in range(num_outputs):
        try:
            output = Output(f"Output{i}", Value="test")
            template.add_output(output)
        except ValueError as e:
            # Should only fail if we exceed MAX_OUTPUTS
            assert num_outputs > troposphere.MAX_OUTPUTS
            assert "Maximum outputs" in str(e)
            return
    
    # If we got here, we should be within the limit
    assert num_outputs <= troposphere.MAX_OUTPUTS


# Test 11: depends_on_helper preserves non-AWSObject values
@given(
    value=st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False),
        st.booleans(),
        st.none(),
        st.lists(st.text(), min_size=0, max_size=5)
    )
)
def test_depends_on_helper_preserves_non_awsobjects(value):
    """Test that depends_on_helper preserves non-AWSObject values unchanged"""
    result = depends_on_helper(value)
    
    if isinstance(value, list):
        # Lists should be processed element-wise
        assert isinstance(result, list)
        assert len(result) == len(value)
        # Each element should be preserved
        for orig, res in zip(value, result):
            assert res == orig
    else:
        # Non-list, non-AWSObject values should be returned unchanged
        assert result == value


# Test 12: Template equality is reflexive
@given(
    description=st.text(min_size=0, max_size=100)
)
def test_template_equality_reflexive(description):
    """Test that Template equality is reflexive: t == t"""
    template = Template(Description=description)
    # Add some resources to make it non-trivial
    template.add_parameter(Parameter("TestParam", Type="String"))
    
    # Template should equal itself
    assert template == template
    assert not (template != template)


# Test 13: Tags from_dict and to_dict round-trip
@given(
    tags_dict=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=10
    )
)
def test_tags_dict_round_trip(tags_dict):
    """Test that Tags.from_dict(tags.to_dict()) preserves data"""
    # Create tags from dict
    tags1 = Tags(**tags_dict)
    
    # Convert to dict representation
    dict_repr = tags1.to_dict()
    
    # Create new tags from the dict representation
    # Note: from_dict expects the dict format, not the list format
    # So we need to convert back
    tags2 = Tags()
    for item in dict_repr:
        if 'Key' in item and 'Value' in item:
            tags2.tags.append(item)
    
    # They should produce the same dict representation
    assert tags1.to_dict() == tags2.to_dict()


if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Running property-based tests for troposphere...")
    print(f"Testing troposphere version: {troposphere.__version__}")
    
    # Run tests with pytest if available
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    exit(result.returncode)