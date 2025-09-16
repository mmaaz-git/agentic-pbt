import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re
from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import inspector, Tags, Template
from troposphere.validators import integer


# Property 1: Integer validator should accept anything convertible to int
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.strip() and (x.strip().lstrip('-').isdigit())),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x))
))
def test_integer_validator_accepts_valid_integers(value):
    """The integer validator should accept any value that can be converted to int."""
    result = integer(value)
    # The validator should return the original value
    assert result == value
    # And it should be convertible to int
    assert isinstance(int(result), int)


@given(st.one_of(
    st.text().filter(lambda x: not (x.strip() and x.strip().lstrip('-').isdigit())),
    st.floats(allow_nan=True),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_rejects_invalid_integers(value):
    """The integer validator should reject values that cannot be converted to int."""
    # Skip values that are actually valid integers
    try:
        int(value)
        assume(False)  # Skip this case - it's actually valid
    except (ValueError, TypeError):
        pass  # This is what we want to test
    
    with pytest.raises(ValueError, match="is not a valid integer"):
        integer(value)


# Property 2: Title validation follows alphanumeric pattern
@given(st.text(min_size=1))
def test_title_validation_property(title_text):
    """Resource titles must match the pattern ^[a-zA-Z0-9]+$ to be valid."""
    valid_pattern = re.compile(r"^[a-zA-Z0-9]+$")
    
    if valid_pattern.match(title_text):
        # Should not raise for valid titles
        target = inspector.AssessmentTarget(title_text)
        assert target.title == title_text
    else:
        # Should raise for invalid titles
        with pytest.raises(ValueError, match='Name .* not alphanumeric'):
            inspector.AssessmentTarget(title_text)


# Property 3: Required properties must be provided for to_dict() to work
@given(
    st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1),
    st.integers(min_value=60, max_value=86400),  # AWS limits: 60s to 24h
    st.lists(st.text(min_size=20), min_size=1, max_size=10)  # Simulate ARNs
)
def test_assessment_template_required_properties(title, duration, rules_arns):
    """AssessmentTemplate requires certain properties to be valid."""
    # Create with all required properties
    template = inspector.AssessmentTemplate(
        title,
        AssessmentTargetArn="arn:aws:inspector:region:account:target/test",
        DurationInSeconds=duration,
        RulesPackageArns=rules_arns
    )
    
    # Should be able to convert to dict without errors
    result = template.to_dict()
    assert result['Type'] == 'AWS::Inspector::AssessmentTemplate'
    assert result['Properties']['DurationInSeconds'] == duration
    assert result['Properties']['RulesPackageArns'] == rules_arns


# Property 4: Optional properties can be omitted
@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1))
def test_assessment_target_optional_properties(title):
    """AssessmentTarget should work with only title (all properties are optional)."""
    target = inspector.AssessmentTarget(title)
    result = target.to_dict()
    assert result['Type'] == 'AWS::Inspector::AssessmentTarget'
    # Properties dict might be empty or minimal since all are optional
    assert 'Properties' in result or result.get('Type')


# Property 5: Type validation for properties
@given(
    st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1),
    st.one_of(
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.floats(allow_nan=True)
    )
)
def test_duration_type_validation(title, invalid_duration):
    """DurationInSeconds should reject non-integer values."""
    # First check that our value is indeed invalid
    try:
        int(invalid_duration)
        assume(False)  # Skip if it's actually valid
    except (TypeError, ValueError):
        pass
    
    template = inspector.AssessmentTemplate(
        title,
        AssessmentTargetArn="arn:aws:inspector:region:account:target/test",
        RulesPackageArns=["arn:aws:inspector:region:account:rulespackage/test"]
    )
    
    # Setting invalid type should raise
    with pytest.raises((TypeError, ValueError)):
        template.DurationInSeconds = invalid_duration


# Property 6: Tags concatenation preserves all tags
@given(
    st.dictionaries(st.text(min_size=1), st.text(), min_size=1),
    st.dictionaries(st.text(min_size=1), st.text(), min_size=1)
)
def test_tags_concatenation_preserves_tags(tags1_dict, tags2_dict):
    """Tags concatenation via + operator should preserve all tags from both objects."""
    tags1 = Tags(tags1_dict)
    tags2 = Tags(tags2_dict)
    
    combined = tags1 + tags2
    combined_dict = combined.to_dict()
    
    # All tags from tags1 should be in combined
    for key, value in tags1_dict.items():
        assert any(tag['Key'] == key and tag['Value'] == value for tag in combined_dict)
    
    # All tags from tags2 should be in combined
    for key, value in tags2_dict.items():
        assert any(tag['Key'] == key and tag['Value'] == value for tag in combined_dict)
    
    # Total number of tags should be sum of both (unless there are duplicates)
    expected_count = len(tags1_dict) + len(tags2_dict)
    assert len(combined_dict) == expected_count


# Property 7: ResourceGroup requires Tags property
@given(
    st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1),
    st.dictionaries(st.text(min_size=1), st.text(), min_size=1)
)
def test_resource_group_requires_tags(title, tags_dict):
    """ResourceGroup requires ResourceGroupTags property."""
    tags = Tags(tags_dict)
    resource_group = inspector.ResourceGroup(title, ResourceGroupTags=tags)
    
    result = resource_group.to_dict()
    assert result['Type'] == 'AWS::Inspector::ResourceGroup'
    assert 'ResourceGroupTags' in result['Properties']
    
    # Verify tags are properly formatted
    tags_list = result['Properties']['ResourceGroupTags']
    for key, value in tags_dict.items():
        assert any(tag['Key'] == key and tag['Value'] == value for tag in tags_list)


if __name__ == "__main__":
    # Run with increased examples for better coverage
    import sys
    sys.exit(pytest.main([__file__, "-v"]))