import math
from hypothesis import assume, given, strategies as st
import pytest
import troposphere.datazone as dz


# Test 1: boolean() function properties
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_valid_inputs(value):
    """Test that boolean() correctly converts documented valid inputs"""
    result = dz.boolean(value)
    assert isinstance(result, bool)
    
    # Verify the mapping is correct
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_invalid_inputs_raise_error(value):
    """Test that boolean() raises ValueError for invalid inputs"""
    with pytest.raises(ValueError):
        dz.boolean(value)


# Test 2: double() function properties
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text().map(lambda x: str(float(hash(x) % 1000000) / 100.0))  # numeric strings
))
def test_double_valid_inputs(value):
    """Test that double() accepts values convertible to float and returns original"""
    result = dz.double(value)
    # The function returns the original value if it's valid
    assert result == value
    # Verify it can be converted to float
    float(value)


@given(st.one_of(
    st.text().filter(lambda x: not x.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit()),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.none()
))  
def test_double_invalid_inputs_raise_error(value):
    """Test that double() raises ValueError for non-numeric inputs"""
    # Filter out accidentally valid numeric strings
    try:
        float(value)
        assume(False)  # Skip if it's actually convertible
    except (ValueError, TypeError):
        pass
    
    with pytest.raises(ValueError):
        dz.double(value)


# Test 3: Special case - double() with NaN and Infinity
@given(st.one_of(
    st.just(float('nan')),
    st.just(float('inf')),
    st.just(float('-inf'))
))
def test_double_special_floats(value):
    """Test that double() handles special float values"""
    result = dz.double(value)
    assert result == value or (math.isnan(result) and math.isnan(value))


# Test 4: Domain to_dict/from_dict round-trip property
@given(
    name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    role=st.text(min_size=20).map(lambda x: f"arn:aws:iam::{abs(hash(x)) % 1000000000000:012d}:role/{x[:20]}"),
    description=st.one_of(st.none(), st.text(max_size=200))
)
def test_domain_to_dict_from_dict_roundtrip(name, role, description):
    """Test that Domain can round-trip through to_dict/from_dict"""
    # Create original domain
    kwargs = {
        'Name': name,
        'DomainExecutionRole': role
    }
    if description is not None:
        kwargs['Description'] = description
    
    original = dz.Domain('TestDomain', **kwargs)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Recreate from dict (using Properties part)
    reconstructed = dz.Domain.from_dict('TestDomain2', dict_repr['Properties'])
    
    # Convert back to dict
    dict_repr2 = reconstructed.to_dict()
    
    # Should be identical except possibly for the title
    assert dict_repr['Properties'] == dict_repr2['Properties']
    assert dict_repr['Type'] == dict_repr2['Type']


# Test 5: DataSource with complex nested properties
@given(
    name=st.text(min_size=1, max_size=100),
    domain_id=st.text(min_size=10).map(lambda x: f"d-{x[:10]}"),
    project_id=st.text(min_size=10).map(lambda x: f"p-{x[:10]}"),
    env_id=st.text(min_size=10).map(lambda x: f"e-{x[:10]}"),
    type_id=st.text(min_size=5, max_size=50),
    type_revision=st.text(min_size=1, max_size=20)
)
def test_datasource_to_dict_from_dict_roundtrip(name, domain_id, project_id, env_id, type_id, type_revision):
    """Test DataSource round-trip with nested properties"""
    
    # Create with required fields
    original = dz.DataSource('TestDataSource',
        Name=name,
        DomainIdentifier=domain_id,
        ProjectIdentifier=project_id,
        EnvironmentIdentifier=env_id,
        Type=type_id,
        TypeRevision=type_revision
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Recreate from dict
    reconstructed = dz.DataSource.from_dict('TestDataSource2', dict_repr['Properties'])
    
    # Convert back to dict
    dict_repr2 = reconstructed.to_dict()
    
    # Properties should be identical
    assert dict_repr['Properties'] == dict_repr2['Properties']
    assert dict_repr['Type'] == dict_repr2['Type']


# Test 6: Property validation - required fields
@given(name=st.text(min_size=1, max_size=100))
def test_domain_missing_required_field_validation(name):
    """Test that Domain validates required fields"""
    # Create domain without required DomainExecutionRole
    domain = dz.Domain('TestDomain', Name=name)
    
    # to_dict with validation should raise error for missing required field
    with pytest.raises(ValueError):
        domain.to_dict(validation=True)
    
    # Without validation it should work
    result = domain.to_dict(validation=False)
    assert 'Name' in result['Properties']
    assert 'DomainExecutionRole' not in result['Properties']


# Test 7: Boolean edge cases with mixed types
@given(st.sampled_from([
    ("TRUE", False),  # All caps variant
    ("True", True),   # Expected true
    ("tRuE", False),  # Mixed case - should fail
    ("FALSE", False), # All caps variant  
    ("False", False), # Expected false
    ("fAlSe", False), # Mixed case - should fail
    (" true", False), # Leading space
    ("true ", False), # Trailing space
    ("", False),      # Empty string
]))
def test_boolean_case_sensitivity_and_whitespace(value_and_should_work):
    """Test boolean() function's case sensitivity and whitespace handling"""
    value, should_work = value_and_should_work
    
    if should_work or value in ["True", "true", "False", "false"]:
        result = dz.boolean(value)
        assert isinstance(result, bool)
    else:
        with pytest.raises(ValueError):
            dz.boolean(value)


# Test 8: Double with numeric string edge cases
@given(st.sampled_from([
    "123",
    "-456",
    "78.90",
    "-12.34",
    "1e10",
    "1E10",
    "-3.14e-10",
    ".5",
    "-.5",
    "5.",
    "+123",
    "+.5"
]))
def test_double_numeric_string_formats(value):
    """Test double() with various numeric string formats"""
    result = dz.double(value)
    assert result == value
    # Verify it's actually convertible
    float_val = float(value)
    assert isinstance(float_val, float)


# Test 9: Complex object with nested properties
@given(
    type_val=st.sampled_from(['IAM_IDC', 'DISABLED']),
    user_assignment=st.one_of(st.none(), st.sampled_from(['AUTOMATIC', 'MANUAL']))
)
def test_single_sign_on_property_roundtrip(type_val, user_assignment):
    """Test SingleSignOn property class round-trip"""
    kwargs = {'Type': type_val}
    if user_assignment is not None:
        kwargs['UserAssignment'] = user_assignment
    
    sso = dz.SingleSignOn(**kwargs)
    dict_repr = sso.to_dict()
    
    # Verify structure
    assert dict_repr['Type'] == type_val
    if user_assignment is not None:
        assert dict_repr['UserAssignment'] == user_assignment
    else:
        assert 'UserAssignment' not in dict_repr


# Test 10: Test integer overflow in double function
@given(st.integers(min_value=-(2**63), max_value=2**63-1))
def test_double_large_integers(value):
    """Test double() with large integers"""
    result = dz.double(value)
    assert result == value
    # Should be convertible to float (may lose precision)
    float(value)