import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import troposphere.billingconductor as bc
from troposphere import validators
import pytest
import math

# Test 1: Boolean validator properties
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts documented valid inputs."""
    result = validators.boolean(value)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False

@given(st.text(min_size=1).filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]))
def test_boolean_validator_invalid_strings(value):
    """Test that boolean validator raises ValueError for invalid strings."""
    with pytest.raises(ValueError):
        validators.boolean(value)

@given(st.integers().filter(lambda x: x not in [0, 1]))
def test_boolean_validator_invalid_integers(value):
    """Test that boolean validator raises ValueError for integers other than 0 and 1."""
    with pytest.raises(ValueError):
        validators.boolean(value)

# Test 2: Double validator properties
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_validator_floats(value):
    """Test that double validator accepts and returns float values unchanged."""
    result = validators.double(value)
    assert result == value

@given(st.integers())
def test_double_validator_integers(value):
    """Test that double validator accepts integers."""
    result = validators.double(value)
    assert result == value

@given(st.text(min_size=1).map(lambda x: str(x)))
def test_double_validator_numeric_strings(value):
    """Test double validator with string inputs."""
    try:
        float_val = float(value)
        result = validators.double(value)
        assert result == value  # Should return unchanged
    except (ValueError, OverflowError):
        # If float() raises, so should double()
        with pytest.raises(ValueError):
            validators.double(value)

# Test 3: Class instantiation and properties
@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)
def test_custom_line_item_flat_charge_details(charge_value):
    """Test CustomLineItemFlatChargeDetails with double property."""
    # The ChargeValue property uses double validator
    flat_charge = bc.CustomLineItemFlatChargeDetails(ChargeValue=charge_value)
    result = flat_charge.to_dict()
    assert 'ChargeValue' in result
    assert result['ChargeValue'] == charge_value

@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=0.0, max_value=100.0)
)
def test_custom_line_item_percentage_charge_details(percentage):
    """Test CustomLineItemPercentageChargeDetails with percentage value."""
    percentage_charge = bc.CustomLineItemPercentageChargeDetails(
        PercentageValue=percentage
    )
    result = percentage_charge.to_dict()
    assert 'PercentageValue' in result
    assert result['PercentageValue'] == percentage

@given(st.booleans())
def test_free_tier_activated(activated):
    """Test FreeTier with boolean property."""
    free_tier = bc.FreeTier(Activated=activated)
    result = free_tier.to_dict()
    assert 'Activated' in result
    assert result['Activated'] == activated

# Test 4: Round-trip property - serialization and deserialization
@given(
    st.lists(st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=57), min_size=12, max_size=12), min_size=1, max_size=10),
    st.booleans()
)
def test_account_grouping_serialization(account_ids, auto_associate):
    """Test AccountGrouping serialization preserves data."""
    grouping = bc.AccountGrouping(
        LinkedAccountIds=account_ids,
        AutoAssociate=auto_associate
    )
    result = grouping.to_dict()
    
    # Check all properties are preserved
    assert result['LinkedAccountIds'] == account_ids
    if auto_associate is not None:
        assert result.get('AutoAssociate') == auto_associate

# Test 5: Properties with optional vs required fields
@given(st.text(min_size=1))
def test_computation_preference_required_field(pricing_plan_arn):
    """Test ComputationPreference with required PricingPlanArn."""
    comp_pref = bc.ComputationPreference(PricingPlanArn=pricing_plan_arn)
    result = comp_pref.to_dict()
    assert result['PricingPlanArn'] == pricing_plan_arn

# Test 6: Edge cases for double validator
@given(st.sampled_from([float('inf'), float('-inf'), float('nan')]))
def test_double_validator_special_floats(value):
    """Test double validator with special float values."""
    if math.isnan(value):
        # NaN should work with double validator since float(nan) works
        result = validators.double(value)
        assert math.isnan(result)
    else:
        # Infinity values should also work
        result = validators.double(value)
        assert result == value

# Test 7: ModifierPercentage in PricingRule (uses double validator)
@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-100.0, max_value=100.0)
)
def test_pricing_rule_modifier_percentage(percentage):
    """Test PricingRule with ModifierPercentage using double validator."""
    pricing_rule = bc.PricingRule(
        'TestRule',
        Name='TestPricingRule',
        Scope='GLOBAL',
        Type='MARKUP',
        ModifierPercentage=percentage
    )
    result = pricing_rule.to_dict()
    props = result.get('Properties', {})
    if percentage is not None:
        assert props.get('ModifierPercentage') == percentage