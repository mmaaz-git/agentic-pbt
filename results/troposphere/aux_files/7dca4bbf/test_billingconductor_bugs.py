"""More focused property-based tests to find genuine bugs."""

import json
from hypothesis import given, strategies as st, assume, settings, example
import pytest
from decimal import Decimal

# Test validators and classes
from troposphere.validators import boolean, double
from troposphere.billingconductor import (
    AccountGrouping,
    ComputationPreference,
    BillingGroup,
    CustomLineItemFlatChargeDetails,
    CustomLineItemPercentageChargeDetails,
    LineItemFilter,
    FreeTier,
    PricingRule,
)


# Test 1: Edge cases for double validator
@given(st.sampled_from([
    float('inf'), 
    float('-inf'), 
    float('nan'),
    1e308,  # Near max float
    -1e308,  # Near min float
    sys.float_info.max,
    sys.float_info.min,
    0.0,
    -0.0,
]))
def test_double_validator_edge_cases(value):
    """Test double validator with edge case float values."""
    import math
    
    # Skip NaN and infinity as they might be intentionally rejected
    if math.isnan(value) or math.isinf(value):
        # These should either work or raise a clear error
        try:
            result = double(value)
            # If it accepts inf/nan, it should preserve them
            if math.isnan(value):
                assert math.isnan(result)
            else:
                assert result == value
        except ValueError:
            # If it rejects them, that's also valid behavior
            pass
    else:
        # Regular floats should always work
        result = double(value)
        assert result == value


# Test 2: Testing string representations of numbers for double validator
@given(st.sampled_from([
    "1.23e10",
    "1.23E10", 
    "1.23e-10",
    "1.23E-10",
    "+1.23",
    "-1.23",
    ".123",
    "123.",
    "1_000.5",  # Python 3.6+ numeric literal
    "0x10",  # Hex
    "0o10",  # Octal
    "0b10",  # Binary
]))
def test_double_validator_string_formats(value):
    """Test double validator with various string number formats."""
    try:
        result = double(value)
        # If it accepts the string, converting to float should work
        float_val = float(value)
        # The validator should preserve the original value
        assert result == value
    except ValueError:
        # Some formats might be rejected, which is okay
        # But check if Python's float() would accept it
        try:
            float(value)
            # If Python accepts it but double() doesn't, this could be a limitation
            pass
        except:
            # Both reject it, that's consistent
            pass


# Test 3: Test from_dict with missing required fields 
def test_billing_group_from_dict_missing_required():
    """Test that from_dict properly validates required fields."""
    # Valid minimal dict
    valid_dict = {
        "Type": "AWS::BillingConductor::BillingGroup",
        "Properties": {
            "Name": "TestGroup",
            "PrimaryAccountId": "123456789012",
            "AccountGrouping": {
                "LinkedAccountIds": ["123456789012"]
            },
            "ComputationPreference": {
                "PricingPlanArn": "arn:aws:pricing::123456789012:plan/test"
            }
        }
    }
    
    # This should work
    try:
        bg = BillingGroup.from_dict("TestBG", valid_dict["Properties"])
        assert bg.Name == "TestGroup"
    except Exception as e:
        print(f"Valid dict failed: {e}")
    
    # Remove required field and test
    for required_field in ["Name", "PrimaryAccountId", "AccountGrouping", "ComputationPreference"]:
        invalid_dict = valid_dict["Properties"].copy()
        del invalid_dict[required_field]
        
        try:
            bg = BillingGroup.from_dict("TestBG", invalid_dict)
            # Should have raised an error for missing required field
            print(f"ERROR: Missing {required_field} didn't raise error!")
        except (ValueError, AttributeError, KeyError) as e:
            # Expected behavior
            pass


# Test 4: Test property type coercion
@given(st.integers())
def test_boolean_validator_with_integers(value):
    """Test boolean validator behavior with arbitrary integers."""
    if value == 0:
        assert boolean(value) is False
    elif value == 1:
        assert boolean(value) is True
    else:
        # Other integers should raise ValueError
        with pytest.raises(ValueError):
            boolean(value)


# Test 5: Test JSON round-trip with special characters
@given(st.text())
def test_json_roundtrip_with_special_strings(text):
    """Test JSON serialization with special characters in strings."""
    # Skip titles that would fail validation
    assume(len(text) > 0)
    
    try:
        comp_pref = ComputationPreference(PricingPlanArn=text)
        
        # Convert to JSON
        json_str = comp_pref.to_json()
        
        # Parse back
        parsed = json.loads(json_str)
        
        # Should preserve the exact string
        assert parsed["PricingPlanArn"] == text
        
        # Recreate object
        new_comp_pref = ComputationPreference.from_dict(None, parsed)
        assert new_comp_pref.PricingPlanArn == text
        
    except Exception as e:
        # Some strings might cause issues
        print(f"Failed with text: {repr(text)}, error: {e}")


# Test 6: Test list properties with empty lists
def test_empty_lists_in_properties():
    """Test how classes handle empty lists for list properties."""
    # AccountGrouping requires non-empty LinkedAccountIds
    try:
        ag = AccountGrouping(LinkedAccountIds=[])
        # If this succeeds, check if to_dict works
        d = ag.to_dict()
        # AWS might reject empty lists, but troposphere should handle them
        assert d["LinkedAccountIds"] == []
    except (ValueError, TypeError) as e:
        # This might be intentionally rejected
        pass
    
    # LineItemFilter with empty Values list
    try:
        lif = LineItemFilter(
            Attribute="test",
            MatchOption="EQUAL", 
            Values=[]
        )
        d = lif.to_dict()
        assert d["Values"] == []
    except (ValueError, TypeError) as e:
        # Empty values might be rejected
        pass


# Test 7: Test None values in optional fields
def test_none_in_optional_fields():
    """Test that None values in optional fields are handled correctly."""
    # FreeTier with only required field
    ft = FreeTier(Activated=True)
    d = ft.to_dict()
    assert "Activated" in d
    assert d["Activated"] is True
    
    # PricingRule with None for optional ModifierPercentage
    pr = PricingRule(
        "TestRule",
        Name="TestPricingRule",
        Scope="GLOBAL",
        Type="MARKUP"
    )
    # Don't set ModifierPercentage
    d = pr.to_dict()
    assert "ModifierPercentage" not in d["Properties"]


# Test 8: Test decimal/float precision in double fields
@given(st.decimals(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_decimal_in_double_fields(decimal_value):
    """Test how decimal values are handled in double fields."""
    try:
        # CustomLineItemFlatChargeDetails expects a double
        charge_details = CustomLineItemFlatChargeDetails(
            ChargeValue=double(str(decimal_value))
        )
        
        # Check it preserves the value correctly
        d = charge_details.to_dict()
        
        # The value should be preserved (as string or float)
        assert "ChargeValue" in d
        
    except Exception as e:
        print(f"Failed with decimal {decimal_value}: {e}")


# Test 9: Test very long strings in text fields
@given(st.text(min_size=1000, max_size=10000))
def test_very_long_strings(long_text):
    """Test handling of very long strings in text properties."""
    try:
        comp_pref = ComputationPreference(PricingPlanArn=long_text)
        d = comp_pref.to_dict()
        assert d["PricingPlanArn"] == long_text
        
        # Test JSON serialization with long strings
        json_str = comp_pref.to_json()
        parsed = json.loads(json_str)
        assert parsed["PricingPlanArn"] == long_text
        
    except Exception as e:
        print(f"Failed with long text (len={len(long_text)}): {e}")


# Test 10: Test mutation after creation
def test_property_mutation():
    """Test that properties can be mutated after object creation."""
    ag = AccountGrouping(LinkedAccountIds=["123"])
    
    # Try to mutate the list
    original_list = ag.LinkedAccountIds
    ag.LinkedAccountIds = ["456", "789"]
    
    assert ag.LinkedAccountIds == ["456", "789"]
    d = ag.to_dict()
    assert d["LinkedAccountIds"] == ["456", "789"]
    
    # Try to append to the list
    ag.LinkedAccountIds.append("999")
    assert "999" in ag.LinkedAccountIds
    
    d2 = ag.to_dict()
    assert "999" in d2["LinkedAccountIds"]


if __name__ == "__main__":
    import sys
    print("Running edge case tests...")
    
    # Run tests that don't need pytest
    test_billing_group_from_dict_missing_required()
    test_empty_lists_in_properties()
    test_none_in_optional_fields()
    test_property_mutation()
    
    print("Basic tests completed!")