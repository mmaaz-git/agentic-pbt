"""Property-based tests for troposphere.cloudformation module."""

import math
from hypothesis import assume, given, strategies as st, settings
import pytest
from troposphere.cloudformation import (
    validate_int_to_str, 
    WaitCondition,
    S3Location,
    Parameter,
    StackNames,
    GuardHook,
    Options,
    AutoDeployment,
    ManagedExecution,
)
from troposphere import Tags


# Test 1: Round-trip property for validate_int_to_str
@given(st.integers(min_value=0, max_value=2**31-1))
def test_validate_int_to_str_with_integers(x):
    """Test that validate_int_to_str handles integers correctly."""
    result = validate_int_to_str(x)
    assert isinstance(result, str)
    assert result == str(x)
    # Round-trip: converting back should give same string
    result2 = validate_int_to_str(result)
    assert result2 == result


@given(st.text(min_size=1).filter(lambda s: s.strip() and s.strip().lstrip('-+').isdigit()))
def test_validate_int_to_str_with_numeric_strings(s):
    """Test that validate_int_to_str handles numeric strings correctly."""
    try:
        # Only test with strings that are valid integers
        int_val = int(s)
        result = validate_int_to_str(s)
        assert isinstance(result, str)
        assert result == str(int_val)
    except ValueError:
        # If conversion fails, the function should raise TypeError
        with pytest.raises(TypeError):
            validate_int_to_str(s)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_validate_int_to_str_rejects_floats(x):
    """Test that validate_int_to_str rejects float values."""
    assume(not x.is_integer())  # Skip integer floats like 1.0
    with pytest.raises(TypeError):
        validate_int_to_str(x)


# Test 2: WaitCondition validation logic
@given(
    count=st.one_of(st.none(), st.integers(min_value=1, max_value=100)),
    handle=st.one_of(st.none(), st.text(min_size=1)),
    timeout=st.one_of(st.none(), st.integers(min_value=1, max_value=3600)),
    has_creation_policy=st.booleans()
)
def test_wait_condition_validation(count, handle, timeout, has_creation_policy):
    """Test WaitCondition validation rules about CreationPolicy conflicts."""
    kwargs = {}
    if count is not None:
        kwargs['Count'] = count
    if handle is not None:
        kwargs['Handle'] = handle
    if timeout is not None:
        kwargs['Timeout'] = timeout
    
    if has_creation_policy:
        # When CreationPolicy is present, no properties should be allowed
        wc = WaitCondition("TestWaitCondition", validation=False, **kwargs)
        wc.resource['CreationPolicy'] = {'ResourceSignal': {'Count': 1, 'Timeout': 'PT5M'}}
        
        if kwargs:  # If any properties are set
            with pytest.raises(ValueError, match="cannot be specified with CreationPolicy"):
                wc.validate()
        else:  # No properties set is fine
            wc.validate()  # Should not raise
    else:
        # Without CreationPolicy, Handle and Timeout are required
        wc = WaitCondition("TestWaitCondition", validation=False, **kwargs)
        
        if handle is not None and timeout is not None:
            wc.validate()  # Should not raise
        else:
            with pytest.raises(ValueError, match="Property .* is required"):
                wc.validate()


# Test 3: Property type validation for S3Location
@given(
    uri=st.one_of(st.text(min_size=1), st.integers(), st.none()),
    version_id=st.one_of(st.text(), st.integers(), st.none())
)
def test_s3location_property_types(uri, version_id):
    """Test that S3Location enforces correct property types."""
    if uri is None:
        # Uri is required, should fail
        with pytest.raises((TypeError, ValueError)):
            S3Location(Uri=uri, VersionId=version_id)
    elif not isinstance(uri, str):
        # Uri must be a string
        with pytest.raises((TypeError, AttributeError)):
            S3Location(Uri=uri, VersionId=version_id)
    else:
        # Valid Uri string
        if version_id is not None and not isinstance(version_id, str):
            with pytest.raises((TypeError, AttributeError)):
                S3Location(Uri=uri, VersionId=version_id)
        else:
            # Should succeed
            s3loc = S3Location(Uri=uri, VersionId=version_id)
            assert s3loc.properties['Uri'] == uri
            if version_id is not None:
                assert s3loc.properties['VersionId'] == version_id


# Test 4: Boolean property validation
@given(
    enabled=st.one_of(st.booleans(), st.text(), st.integers()),
    retain_stacks=st.one_of(st.booleans(), st.text(), st.integers())
)
def test_autodeployment_boolean_properties(enabled, retain_stacks):
    """Test that AutoDeployment correctly validates boolean properties."""
    kwargs = {}
    if enabled is not None:
        kwargs['Enabled'] = enabled
    if retain_stacks is not None:
        kwargs['RetainStacksOnAccountRemoval'] = retain_stacks
    
    # Both properties are optional booleans
    valid = True
    if enabled is not None and not isinstance(enabled, bool):
        valid = False
    if retain_stacks is not None and not isinstance(retain_stacks, bool):
        valid = False
    
    if valid:
        ad = AutoDeployment(**kwargs)
        if enabled is not None:
            assert ad.properties['Enabled'] == enabled
        if retain_stacks is not None:
            assert ad.properties['RetainStacksOnAccountRemoval'] == retain_stacks
    else:
        with pytest.raises((TypeError, AttributeError)):
            AutoDeployment(**kwargs)


# Test 5: Parameter key-value requirement
@given(
    key=st.one_of(st.text(min_size=1), st.none()),
    value=st.one_of(st.text(), st.none())
)
def test_parameter_required_fields(key, value):
    """Test that Parameter enforces both ParameterKey and ParameterValue as required."""
    if key is None or value is None:
        # Both fields are required
        with pytest.raises((TypeError, ValueError)):
            Parameter(ParameterKey=key, ParameterValue=value)
    else:
        param = Parameter(ParameterKey=key, ParameterValue=value)
        assert param.properties['ParameterKey'] == key
        assert param.properties['ParameterValue'] == value


# Test 6: StackNames Include/Exclude lists
@given(
    include=st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=0, max_size=10)),
    exclude=st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=0, max_size=10))
)
def test_stacknames_list_properties(include, exclude):
    """Test that StackNames correctly handles list properties."""
    kwargs = {}
    if include is not None:
        kwargs['Include'] = include
    if exclude is not None:
        kwargs['Exclude'] = exclude
    
    sn = StackNames(**kwargs)
    if include is not None:
        assert sn.properties['Include'] == include
    if exclude is not None:
        assert sn.properties['Exclude'] == exclude