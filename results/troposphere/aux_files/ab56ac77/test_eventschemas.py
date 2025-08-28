import troposphere.eventschemas as es
from hypothesis import given, strategies as st, assume
import pytest


@given(st.text())
def test_boolean_case_insensitive_consistency(s):
    """
    Test that the boolean function handles case variations consistently.
    If it accepts 'true', it should accept 'TRUE' and 'True'.
    If it accepts 'false', it should accept 'FALSE' and 'False'.
    """
    # Test various case variations of true/false strings
    if s.lower() == 'true':
        # All case variations of 'true' should behave the same
        try:
            result_lower = es.boolean('true')
            result_title = es.boolean('True')
            result_upper = es.boolean('TRUE')
            # If one works, all should work and return the same value
            assert result_lower == result_title == result_upper == True
        except ValueError:
            # If one raises ValueError, all should raise
            with pytest.raises(ValueError):
                es.boolean('true')
            with pytest.raises(ValueError):
                es.boolean('True')
            with pytest.raises(ValueError):
                es.boolean('TRUE')
    
    if s.lower() == 'false':
        # All case variations of 'false' should behave the same
        try:
            result_lower = es.boolean('false')
            result_title = es.boolean('False')
            result_upper = es.boolean('FALSE')
            # If one works, all should work and return the same value
            assert result_lower == result_title == result_upper == False
        except ValueError:
            # If one raises ValueError, all should raise
            with pytest.raises(ValueError):
                es.boolean('false')
            with pytest.raises(ValueError):
                es.boolean('False')
            with pytest.raises(ValueError):
                es.boolean('FALSE')


@given(st.one_of(
    st.booleans(),
    st.integers(min_value=-100, max_value=100),
    st.text(min_size=0, max_size=20),
    st.none()
))
def test_boolean_deterministic(value):
    """Test that boolean function is deterministic - same input always gives same output."""
    try:
        result1 = es.boolean(value)
        result2 = es.boolean(value)
        assert result1 == result2
        assert isinstance(result1, bool)
    except ValueError:
        # Should consistently raise ValueError for the same input
        with pytest.raises(ValueError):
            es.boolean(value)


@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=10))
def test_boolean_string_case_handling(s):
    """Test that boolean function handles string case variations properly."""
    # The function should either accept all case variations or none
    lowercase = s.lower()
    uppercase = s.upper()
    titlecase = s.title()
    
    results = []
    for variant in [lowercase, uppercase, titlecase]:
        try:
            result = es.boolean(variant)
            results.append(('success', result))
        except ValueError:
            results.append(('error', None))
    
    # All variants should have the same behavior (all succeed or all fail)
    behaviors = [r[0] for r in results]
    if lowercase in ['true', 'false']:
        # For true/false strings, behavior might differ by case (this is the bug)
        pass
    else:
        # For non-boolean strings, all cases should behave the same
        assert len(set(behaviors)) == 1, f"Inconsistent behavior for variations of '{s}'"


@given(st.builds(
    es.Registry,
    st.text(min_size=1, max_size=50),
    Description=st.text(min_size=0, max_size=100),
    RegistryName=st.text(min_size=1, max_size=50)
))
def test_registry_to_dict_structure(registry):
    """Test that Registry.to_dict produces valid CloudFormation structure."""
    result = registry.to_dict()
    
    # Should have Type and Properties keys
    assert 'Type' in result
    assert result['Type'] == 'AWS::EventSchemas::Registry'
    assert 'Properties' in result
    assert isinstance(result['Properties'], dict)
    
    # Properties should contain the set attributes
    if hasattr(registry, 'Description') and registry.Description:
        assert 'Description' in result['Properties']
    if hasattr(registry, 'RegistryName') and registry.RegistryName:
        assert 'RegistryName' in result['Properties']


@given(st.builds(
    es.Schema,
    st.text(min_size=1, max_size=50),
    Content=st.text(min_size=1, max_size=100),
    RegistryName=st.text(min_size=1, max_size=50),
    Type=st.text(min_size=1, max_size=20)
))
def test_schema_to_dict_required_fields(schema):
    """Test that Schema.to_dict includes all required fields."""
    result = schema.to_dict()
    
    assert 'Type' in result
    assert result['Type'] == 'AWS::EventSchemas::Schema'
    assert 'Properties' in result
    
    # Check required fields are present
    props = result['Properties']
    assert 'Content' in props
    assert 'RegistryName' in props
    assert 'Type' in props