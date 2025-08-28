import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import troposphere.billingconductor as bc
from troposphere import validators
import pytest
import math

# Test validation behavior when calling to_dict(validation=True)
def test_billing_group_missing_required_fields():
    """Test that BillingGroup without required fields fails validation."""
    bg = bc.BillingGroup('TestGroup')
    # to_dict() with validation=True should raise an error for missing required props
    with pytest.raises(ValueError) as exc_info:
        bg.to_dict(validation=True)
    assert "Resource TestGroup required in Properties" in str(exc_info.value)

def test_billing_group_validate_method():
    """Test that validate() method works correctly."""
    bg = bc.BillingGroup('TestGroup')
    # The validate method should raise an error for missing required props
    with pytest.raises(ValueError) as exc_info:
        bg.validate()
    assert "Resource TestGroup required in Properties" in str(exc_info.value)

# Test property type validation
@given(st.integers())
def test_account_grouping_type_validation(invalid_value):
    """Test that AccountGrouping validates LinkedAccountIds type."""
    # LinkedAccountIds should be a list, not an integer
    try:
        grouping = bc.AccountGrouping(LinkedAccountIds=invalid_value)
        # If it doesn't raise immediately, check on to_dict()
        result = grouping.to_dict()
        # If it's an iterable (like range), it might work
        assert hasattr(invalid_value, '__iter__')
    except (TypeError, AttributeError):
        # Expected to fail for non-iterables
        pass

# Test double validator with edge cases around float parsing
@given(st.text())
def test_double_validator_random_strings(text):
    """Test double validator with random strings."""
    try:
        float_val = float(text)
        # If float() succeeds, double() should too
        result = validators.double(text)
        assert result == text
    except (ValueError, TypeError, OverflowError):
        # If float() fails, double() should also fail
        with pytest.raises(ValueError):
            validators.double(text)

# Test boolean validator consistency
@given(st.one_of(st.integers(), st.floats(), st.text(), st.booleans()))
def test_boolean_validator_consistency(value):
    """Test that boolean validator is consistent."""
    try:
        result1 = validators.boolean(value)
        result2 = validators.boolean(value)
        # Multiple calls should return same result
        assert result1 == result2
    except ValueError:
        # If it raises once, it should always raise
        with pytest.raises(ValueError):
            validators.boolean(value)

# Test property inheritance and overriding
def test_aws_object_property_override():
    """Test that properties can be overridden after initialization."""
    bg = bc.BillingGroup(
        'TestGroup',
        Name='InitialName',
        PrimaryAccountId='123',
        AccountGrouping=bc.AccountGrouping(LinkedAccountIds=['456']),
        ComputationPreference=bc.ComputationPreference(PricingPlanArn='arn:test')
    )
    
    # Override a property
    bg.Name = 'UpdatedName'
    result = bg.to_dict()
    assert result['Properties']['Name'] == 'UpdatedName'

# Test with special characters in string properties
@given(st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))
def test_string_properties_with_special_chars(text):
    """Test string properties with special characters."""
    try:
        bg = bc.BillingGroup(
            'TestGroup',
            Name=text,
            PrimaryAccountId='123',
            AccountGrouping=bc.AccountGrouping(LinkedAccountIds=['456']),
            ComputationPreference=bc.ComputationPreference(PricingPlanArn='arn:test')
        )
        result = bg.to_dict()
        assert result['Properties']['Name'] == text
    except Exception as e:
        # Some characters might cause issues
        pass

# Test LineItemFilter with various attribute values
@given(
    st.text(min_size=1),
    st.text(min_size=1),
    st.lists(st.text(min_size=1), min_size=1)
)
def test_line_item_filter_properties(attr, match, values):
    """Test LineItemFilter with various values."""
    filter_obj = bc.LineItemFilter(
        Attribute=attr,
        MatchOption=match,
        Values=values
    )
    result = filter_obj.to_dict()
    assert result['Attribute'] == attr
    assert result['MatchOption'] == match
    assert result['Values'] == values

# Test CustomLineItemChargeDetails with mutually exclusive properties
def test_custom_line_item_charge_details_mutual_exclusion():
    """Test CustomLineItemChargeDetails with both Flat and Percentage."""
    # Can we set both Flat and Percentage?
    charge_details = bc.CustomLineItemChargeDetails(
        Type='PERCENTAGE',
        Flat=bc.CustomLineItemFlatChargeDetails(ChargeValue=100.0),
        Percentage=bc.CustomLineItemPercentageChargeDetails(PercentageValue=10.0)
    )
    result = charge_details.to_dict()
    # Both should be present in the dict
    assert 'Flat' in result
    assert 'Percentage' in result
    assert result['Type'] == 'PERCENTAGE'

# Test PricingRule with all optional fields
@given(
    st.text(min_size=1),
    st.text(min_size=1),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=1),
    st.text(min_size=1),
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_pricing_rule_all_fields(name, desc, modifier, billing_entity, operation, service, usage_type):
    """Test PricingRule with all optional fields."""
    rule = bc.PricingRule(
        'TestRule',
        Name=name,
        Scope='GLOBAL',
        Type='MARKUP',
        Description=desc,
        ModifierPercentage=modifier,
        BillingEntity=billing_entity,
        Operation=operation,
        Service=service,
        UsageType=usage_type
    )
    result = rule.to_dict()
    props = result['Properties']
    assert props['Name'] == name
    assert props['Description'] == desc
    assert props['ModifierPercentage'] == modifier
    assert props['BillingEntity'] == billing_entity

# Test to_json method
def test_to_json_serialization():
    """Test that to_json produces valid JSON."""
    import json
    
    bg = bc.BillingGroup(
        'TestGroup',
        Name='Test',
        PrimaryAccountId='123',
        AccountGrouping=bc.AccountGrouping(LinkedAccountIds=['456']),
        ComputationPreference=bc.ComputationPreference(PricingPlanArn='arn:test')
    )
    
    json_str = bg.to_json()
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed['Type'] == 'AWS::BillingConductor::BillingGroup'
    assert parsed['Properties']['Name'] == 'Test'

# Test FreeTier with Tiering
def test_tiering_with_free_tier():
    """Test Tiering with FreeTier property."""
    tiering = bc.Tiering(FreeTier=bc.FreeTier(Activated=True))
    result = tiering.to_dict()
    assert result['FreeTier']['Activated'] is True
    
    tiering2 = bc.Tiering(FreeTier=bc.FreeTier(Activated=False))
    result2 = tiering2.to_dict()
    assert result2['FreeTier']['Activated'] is False