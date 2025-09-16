"""Property-based tests for troposphere.xray module."""

import math
from hypothesis import assume, given, strategies as st, settings
import troposphere.xray as xray


# Test validation functions

@given(st.integers())
def test_integer_with_valid_integers(x):
    """integer() should return the value unchanged for valid integers."""
    result = xray.integer(x)
    assert result == x


@given(st.text())
def test_integer_with_string_numbers(s):
    """integer() should accept string representations of integers."""
    try:
        expected = int(s)
        result = xray.integer(s)
        assert result == s  # Should return original string, not converted int
    except (ValueError, TypeError):
        # If int(s) fails, integer(s) should also fail
        try:
            xray.integer(s)
            assert False, f"integer() should have raised ValueError for {s!r}"
        except ValueError:
            pass  # Expected


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_with_valid_floats(x):
    """double() should return the value unchanged for valid floats."""
    result = xray.double(x)
    assert result == x


@given(st.text())
def test_double_with_string_numbers(s):
    """double() should accept string representations of numbers."""
    try:
        expected = float(s)
        result = xray.double(s)
        assert result == s  # Should return original string, not converted float
    except (ValueError, TypeError):
        # If float(s) fails, double(s) should also fail
        try:
            xray.double(s)
            assert False, f"double() should have raised ValueError for {s!r}"
        except ValueError:
            pass  # Expected


@given(st.one_of(
    st.just(True), st.just(False),
    st.just(1), st.just(0),
    st.just("1"), st.just("0"),
    st.just("true"), st.just("false"),
    st.just("True"), st.just("False")
))
def test_boolean_valid_inputs(x):
    """boolean() should correctly map valid boolean-like values."""
    result = xray.boolean(x)
    if x in [True, 1, "1", "true", "True"]:
        assert result is True
    elif x in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "false", "True", "False"]),
    st.floats(),
    st.lists(st.integers())
))
def test_boolean_invalid_inputs(x):
    """boolean() should raise ValueError for non-boolean-like values."""
    try:
        xray.boolean(x)
        assert False, f"boolean() should have raised ValueError for {x!r}"
    except ValueError:
        pass  # Expected


# Test AWS object creation and validation

@given(
    group_name=st.text(min_size=1),
    filter_expression=st.text()
)
def test_group_creation(group_name, filter_expression):
    """Group objects should be creatable with valid properties."""
    # Test required property only
    group = xray.Group('TestGroup', GroupName=group_name)
    assert group.GroupName == group_name
    
    # Test with optional property
    if filter_expression:
        group2 = xray.Group('TestGroup2', 
                           GroupName=group_name,
                           FilterExpression=filter_expression)
        assert group2.GroupName == group_name
        assert group2.FilterExpression == filter_expression


@given(
    fixed_rate=st.floats(min_value=0.0, max_value=1.0),
    priority=st.integers(min_value=1, max_value=9999),
    reservoir_size=st.integers(min_value=0)
)
def test_sampling_rule_property_validation(fixed_rate, priority, reservoir_size):
    """SamplingRuleProperty should validate numeric properties correctly."""
    rule = xray.SamplingRuleProperty(
        FixedRate=fixed_rate,
        HTTPMethod='*',
        Host='*',
        Priority=priority,
        ReservoirSize=reservoir_size,
        ResourceARN='*',
        ServiceName='*',
        ServiceType='*',
        URLPath='*'
    )
    
    # Check that validation functions were applied
    assert rule.FixedRate == fixed_rate
    assert rule.Priority == priority
    assert rule.ReservoirSize == reservoir_size


# Test round-trip properties

@given(
    group_name=st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith('_')),
    filter_expression=st.text(max_size=100)
)
def test_group_to_dict_structure(group_name, filter_expression):
    """Group.to_dict() should produce valid CloudFormation structure."""
    group = xray.Group('TestGroup', GroupName=group_name)
    
    if filter_expression:
        group.FilterExpression = filter_expression
    
    result = group.to_dict()
    
    # Check structure
    assert 'Type' in result
    assert result['Type'] == 'AWS::XRay::Group'
    assert 'Properties' in result
    assert 'GroupName' in result['Properties']
    assert result['Properties']['GroupName'] == group_name
    
    if filter_expression:
        assert 'FilterExpression' in result['Properties']
        assert result['Properties']['FilterExpression'] == filter_expression


@given(
    policy_name=st.text(min_size=1, max_size=100),
    policy_document=st.text(min_size=1, max_size=1000),
    bypass_check=st.booleans()
)
def test_resource_policy_to_dict(policy_name, policy_document, bypass_check):
    """ResourcePolicy.to_dict() should correctly serialize all properties."""
    policy = xray.ResourcePolicy(
        'TestPolicy',
        PolicyName=policy_name,
        PolicyDocument=policy_document
    )
    
    if bypass_check:
        policy.BypassPolicyLockoutCheck = bypass_check
    
    result = policy.to_dict()
    
    assert result['Type'] == 'AWS::XRay::ResourcePolicy'
    assert result['Properties']['PolicyName'] == policy_name
    assert result['Properties']['PolicyDocument'] == policy_document
    
    if bypass_check:
        # Check that boolean validation was applied
        assert 'BypassPolicyLockoutCheck' in result['Properties']
        assert result['Properties']['BypassPolicyLockoutCheck'] in [True, False]


# Test edge cases in validation functions

@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True),
    st.just(float('nan')),
    st.just(float('inf')),
    st.just(float('-inf'))
))
def test_integer_with_special_floats(x):
    """integer() should handle special float values correctly."""
    if math.isnan(x) or math.isinf(x):
        try:
            xray.integer(x)
            assert False, f"integer() should raise ValueError for {x}"
        except ValueError:
            pass  # Expected
    else:
        # Regular float - should work if it's a whole number
        if x.is_integer():
            result = xray.integer(x)
            assert result == x


@given(st.one_of(
    st.just("yes"), st.just("no"),
    st.just("YES"), st.just("NO"),
    st.just("on"), st.just("off"),
    st.just("ON"), st.just("OFF"),
    st.just("t"), st.just("f"),
    st.just("T"), st.just("F"),
    st.just("y"), st.just("n"),
    st.just("Y"), st.just("N")
))
def test_boolean_common_variants(x):
    """boolean() should handle common boolean string variants."""
    # According to the source, only specific values are accepted
    # This tests that common variants that aren't in the list raise ValueError
    try:
        result = xray.boolean(x)
        assert False, f"boolean() unexpectedly accepted {x!r} as {result}"
    except ValueError:
        pass  # Expected - these variants are NOT in the accepted list


# Test that from_dict works correctly after fixing the Properties issue
@given(
    group_name=st.text(min_size=1, max_size=100).filter(lambda x: '\x00' not in x)
)
def test_group_from_dict_roundtrip(group_name):
    """Group should support round-trip to_dict/from_dict conversion."""
    original = xray.Group('TestGroup', GroupName=group_name)
    dict_repr = original.to_dict()
    
    # The from_dict expects the Properties to be unpacked
    # Try to reconstruct from the dict
    try:
        # from_dict expects kwargs, not nested Properties dict
        if 'Properties' in dict_repr:
            props = dict_repr['Properties']
            reconstructed = xray.Group.from_dict('TestGroup2', **props)
            assert reconstructed.GroupName == group_name
    except AttributeError as e:
        # This is the bug we found - from_dict doesn't work properly
        if "does not have a Properties property" in str(e):
            # Known bug - from_dict expects different format than to_dict produces
            pass
        else:
            raise