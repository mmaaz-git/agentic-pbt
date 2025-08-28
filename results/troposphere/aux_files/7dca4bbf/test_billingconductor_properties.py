"""Property-based tests for troposphere.billingconductor module."""

import json
from hypothesis import given, strategies as st, assume, settings
import pytest

# Test validators
from troposphere.validators import boolean, double

# Test the billingconductor module classes
from troposphere.billingconductor import (
    AccountGrouping,
    ComputationPreference,
    BillingGroup,
    BillingPeriodRange,
    CustomLineItemFlatChargeDetails,
    CustomLineItemPercentageChargeDetails,
    LineItemFilter,
    CustomLineItemChargeDetails,
    CustomLineItem,
    PricingPlan,
    FreeTier,
    Tiering,
    PricingRule,
)


# Test 1: Boolean validator idempotence property
@given(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False", "1", "0"]))
def test_boolean_validator_idempotence(value):
    """Test that boolean() is idempotent - applying it twice gives same result."""
    first_result = boolean(value)
    second_result = boolean(first_result)
    assert first_result == second_result
    assert isinstance(first_result, bool)
    assert isinstance(second_result, bool)


# Test 2: Boolean validator correctness
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_validator_true_values(value):
    """Test that boolean() correctly converts truthy values to True."""
    assert boolean(value) is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_validator_false_values(value):
    """Test that boolean() correctly converts falsy values to False."""
    assert boolean(value) is False


# Test 3: Double validator accepts valid floats
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_validator_accepts_floats(value):
    """Test that double() accepts valid float values."""
    result = double(value)
    assert result == value


@given(st.integers())
def test_double_validator_accepts_integers(value):
    """Test that double() accepts integer values (as they can be floats)."""
    result = double(value)
    assert result == value


# Test 4: Property validation for required fields
@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_account_grouping_required_fields(account_ids):
    """Test that AccountGrouping requires LinkedAccountIds."""
    # Should succeed with required field
    obj = AccountGrouping(LinkedAccountIds=account_ids)
    assert obj.LinkedAccountIds == account_ids
    
    # to_dict should not fail for valid object
    d = obj.to_dict()
    assert "LinkedAccountIds" in d


@given(st.text(min_size=1))
def test_computation_preference_required_fields(arn):
    """Test that ComputationPreference requires PricingPlanArn."""
    obj = ComputationPreference(PricingPlanArn=arn)
    assert obj.PricingPlanArn == arn
    
    d = obj.to_dict()
    assert "PricingPlanArn" in d


# Test 5: BillingGroup creation with required fields
@given(
    st.text(min_size=1, alphabet=st.characters(whitelist_categories=["L", "N"])),
    st.text(min_size=1),
    st.text(min_size=1),
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.text(min_size=1)
)
def test_billing_group_creation(title, name, primary_account_id, linked_account_ids, pricing_plan_arn):
    """Test BillingGroup creation with all required fields."""
    # Filter to alphanumeric title as required by AWS
    assume(title.isalnum())
    
    account_grouping = AccountGrouping(LinkedAccountIds=linked_account_ids)
    computation_pref = ComputationPreference(PricingPlanArn=pricing_plan_arn)
    
    billing_group = BillingGroup(
        title,
        Name=name,
        PrimaryAccountId=primary_account_id,
        AccountGrouping=account_grouping,
        ComputationPreference=computation_pref
    )
    
    assert billing_group.title == title
    assert billing_group.Name == name
    assert billing_group.PrimaryAccountId == primary_account_id
    
    # Test to_dict doesn't fail
    d = billing_group.to_dict()
    assert d["Type"] == "AWS::BillingConductor::BillingGroup"
    assert "Properties" in d


# Test 6: CustomLineItemFlatChargeDetails with double values
@given(st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_custom_line_item_flat_charge_details(charge_value):
    """Test CustomLineItemFlatChargeDetails with double validator."""
    obj = CustomLineItemFlatChargeDetails(ChargeValue=double(charge_value))
    assert obj.ChargeValue == charge_value
    
    d = obj.to_dict()
    assert "ChargeValue" in d


# Test 7: CustomLineItemPercentageChargeDetails with percentage values
@given(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
def test_custom_line_item_percentage_charge_details(percentage):
    """Test CustomLineItemPercentageChargeDetails with percentage values."""
    obj = CustomLineItemPercentageChargeDetails(PercentageValue=double(percentage))
    assert obj.PercentageValue == percentage
    
    d = obj.to_dict()
    assert "PercentageValue" in d


# Test 8: LineItemFilter properties
@given(
    st.text(min_size=1),
    st.sampled_from(["EQUAL", "NOT_EQUAL", "CONTAINS", "NOT_CONTAINS"]),
    st.lists(st.text(min_size=1), min_size=1, max_size=5)
)
def test_line_item_filter(attribute, match_option, values):
    """Test LineItemFilter with required fields."""
    obj = LineItemFilter(
        Attribute=attribute,
        MatchOption=match_option,
        Values=values
    )
    
    assert obj.Attribute == attribute
    assert obj.MatchOption == match_option
    assert obj.Values == values
    
    d = obj.to_dict()
    assert all(k in d for k in ["Attribute", "MatchOption", "Values"])


# Test 9: FreeTier boolean property
@given(st.booleans())
def test_free_tier_activated(activated):
    """Test FreeTier with boolean Activated property."""
    obj = FreeTier(Activated=boolean(activated))
    assert obj.Activated == activated
    
    d = obj.to_dict()
    assert "Activated" in d
    assert d["Activated"] == activated


# Test 10: PricingRule with optional ModifierPercentage
@given(
    st.text(min_size=1, alphabet=st.characters(whitelist_categories=["L", "N"])),
    st.text(min_size=1),
    st.sampled_from(["GLOBAL", "SERVICE", "BILLING_ENTITY", "SKU"]),
    st.sampled_from(["MARKUP", "DISCOUNT", "TIERING"]),
    st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False) | st.none()
)
def test_pricing_rule_creation(title, name, scope, rule_type, modifier_percentage):
    """Test PricingRule creation with optional ModifierPercentage."""
    assume(title.isalnum())
    
    kwargs = {
        "Name": name,
        "Scope": scope,
        "Type": rule_type
    }
    
    if modifier_percentage is not None:
        kwargs["ModifierPercentage"] = double(modifier_percentage)
    
    pricing_rule = PricingRule(title, **kwargs)
    
    assert pricing_rule.title == title
    assert pricing_rule.Name == name
    assert pricing_rule.Scope == scope
    assert pricing_rule.Type == rule_type
    
    if modifier_percentage is not None:
        assert pricing_rule.ModifierPercentage == modifier_percentage
    
    d = pricing_rule.to_dict()
    assert d["Type"] == "AWS::BillingConductor::PricingRule"


# Test 11: Round-trip property for simple properties
@given(st.text(min_size=1))
def test_computation_preference_dict_roundtrip(arn):
    """Test that ComputationPreference survives to_dict and from_dict."""
    original = ComputationPreference(PricingPlanArn=arn)
    dict_repr = original.to_dict()
    
    # Recreate from dict
    reconstructed = ComputationPreference.from_dict(None, dict_repr)
    
    # Should have same properties
    assert reconstructed.PricingPlanArn == original.PricingPlanArn
    assert reconstructed.to_dict() == original.to_dict()


# Test 12: JSON serialization round-trip
@given(st.lists(st.text(min_size=1), min_size=1, max_size=5))
def test_account_grouping_json_roundtrip(account_ids):
    """Test AccountGrouping survives JSON serialization."""
    original = AccountGrouping(LinkedAccountIds=account_ids)
    
    # Convert to JSON and back
    json_str = original.to_json()
    parsed = json.loads(json_str)
    
    # Recreate from parsed dict
    reconstructed = AccountGrouping.from_dict(None, parsed)
    
    assert reconstructed.LinkedAccountIds == original.LinkedAccountIds


# Test 13: Test invalid boolean values raise exceptions
@given(st.text().filter(lambda x: x not in ["true", "false", "True", "False", "0", "1"]))
def test_boolean_validator_invalid_values(value):
    """Test that boolean() raises ValueError for invalid inputs."""
    assume(value not in ["true", "false", "True", "False", "0", "1"])
    with pytest.raises(ValueError):
        boolean(value)


# Test 14: Test invalid double values raise exceptions  
@given(st.text(alphabet=st.characters(blacklist_categories=["Nd"])).filter(lambda x: not x.replace(".", "").replace("-", "").isdigit()))
def test_double_validator_invalid_values(value):
    """Test that double() raises ValueError for non-numeric inputs."""
    assume(value != "" and value != "-" and value != ".")
    with pytest.raises(ValueError):
        double(value)


if __name__ == "__main__":
    # Run a quick smoke test
    test_boolean_validator_idempotence()
    test_double_validator_accepts_floats()
    test_billing_group_creation()
    print("Basic tests passed!")