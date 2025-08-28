import math
from hypothesis import given, strategies as st, assume, settings, note
import troposphere.route53recoverycontrol as r53rc
from troposphere.validators import boolean, integer
from troposphere import Template

# Test edge cases in boolean validator
def test_boolean_edge_cases():
    """Test edge cases for boolean validator"""
    # Test that values not in the expected set raise ValueError
    invalid_values = [2, -1, "yes", "no", "TRUE", "FALSE", [], {}, None, 2.5]
    for value in invalid_values:
        try:
            result = boolean(value)
            print(f"UNEXPECTED: boolean({value}) returned {result} instead of raising")
        except ValueError:
            pass  # Expected
        except Exception as e:
            print(f"UNEXPECTED: boolean({value}) raised {type(e).__name__}: {e}")

# Test edge cases in integer validator
def test_integer_edge_cases():
    """Test edge cases for integer validator"""
    # Test with very large integers
    large_int = 2**100
    result = integer(large_int)
    assert int(result) == large_int
    
    # Test with negative integers
    result = integer(-42)
    assert int(result) == -42
    
    # Test with float that's an integer
    result = integer(42.0)
    assert int(result) == 42
    
    # Test with string integers
    result = integer("123")
    assert int(result) == 123
    
    # Test with negative string integers
    result = integer("-456")
    assert int(result) == -456
    
    # Test with special values that should fail
    invalid_values = [None, [], {}, "abc", "12.34", math.nan, math.inf, -math.inf]
    for value in invalid_values:
        try:
            result = integer(value)
            print(f"UNEXPECTED: integer({value}) returned {result} instead of raising")
        except (ValueError, TypeError, OverflowError):
            pass  # Expected

# Test title validation
@given(st.text())
def test_title_validation(title):
    """Test that title validation works correctly"""
    valid = title and all(c.isalnum() for c in title)
    
    try:
        cluster = r53rc.Cluster(title=title, Name="TestName")
        # If we get here, the title was accepted
        assert valid, f"Invalid title '{title}' was accepted"
    except ValueError as e:
        # Title was rejected
        assert not valid or not title, f"Valid title '{title}' was rejected: {e}"

# Test property type checking
def test_property_type_validation():
    """Test that property types are validated"""
    # Test that WaitPeriodMs must be convertible to integer
    try:
        rule = r53rc.AssertionRule(
            AssertedControls=["control1"],
            WaitPeriodMs=[1, 2, 3]  # Should fail - list not integer
        )
        print(f"UNEXPECTED: List was accepted for WaitPeriodMs")
    except (TypeError, ValueError):
        pass  # Expected
    
    # Test that AssertedControls must be a list
    try:
        rule = r53rc.AssertionRule(
            AssertedControls="control1",  # Should fail - string not list
            WaitPeriodMs=1000
        )
        print(f"UNEXPECTED: String was accepted for AssertedControls")
    except (TypeError, ValueError):
        pass  # Expected

# Test to_dict functionality
def test_to_dict_conversion():
    """Test that objects can be converted to dict representation"""
    cluster = r53rc.Cluster(title="MyCluster", Name="TestCluster")
    
    # Call to_dict
    result = cluster.to_dict()
    assert isinstance(result, dict)
    assert result.get("Type") == "AWS::Route53RecoveryControl::Cluster"
    assert result.get("Properties", {}).get("Name") == "TestCluster"
    
    # Test with properties
    rule_config = r53rc.RuleConfig(
        Inverted=True,
        Threshold=5,
        Type="AND"
    )
    safety_rule = r53rc.SafetyRule(
        title="MySafetyRule",
        Name="TestRule",
        ControlPanelArn="arn:aws:...",
        RuleConfig=rule_config
    )
    result = safety_rule.to_dict()
    assert isinstance(result, dict)
    assert result.get("Type") == "AWS::Route53RecoveryControl::SafetyRule"
    
# Test template integration
def test_template_integration():
    """Test that resources can be added to templates"""
    template = Template()
    
    # Add a cluster to the template
    cluster = r53rc.Cluster(
        title="MyCluster",
        template=template,
        Name="TestCluster"
    )
    
    # Check that it was added
    assert "MyCluster" in template.resources
    assert template.resources["MyCluster"] == cluster
    
    # Add another resource
    panel = r53rc.ControlPanel(
        title="MyPanel",
        template=template,
        Name="TestPanel"
    )
    
    assert "MyPanel" in template.resources
    assert len(template.resources) == 2

# Run all edge case tests
if __name__ == "__main__":
    print("Testing boolean edge cases...")
    test_boolean_edge_cases()
    
    print("\nTesting integer edge cases...")
    test_integer_edge_cases()
    
    print("\nTesting property type validation...")
    test_property_type_validation()
    
    print("\nTesting to_dict conversion...")
    test_to_dict_conversion()
    
    print("\nTesting template integration...")
    test_template_integration()
    
    print("\nRunning property-based title validation...")
    test_title_validation()
    
    print("\nAll edge case tests completed!")