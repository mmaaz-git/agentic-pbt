"""Test demonstrating title validation bypass bug in troposphere"""

from hypothesis import given, strategies as st
import troposphere.events as events


@given(st.sampled_from([None, ""]))
def test_title_validation_bypass(title):
    """
    Test that demonstrates title validation bypass bug.
    
    When title is None or empty string, validation is skipped during __init__,
    but validate_title() itself would reject these values if called directly.
    
    This creates inconsistent behavior where invalid titles can be used
    if they're falsy, bypassing the alphanumeric requirement.
    """
    # Object creation succeeds (validation skipped)
    eb = events.EventBus(title, Name='test')
    
    # But the title is actually invalid according to validate_title
    try:
        eb.validate_title()
        # Should never get here for None or empty string
        assert False, f"validate_title() should have failed for {title!r}"
    except ValueError as e:
        # This proves the title is invalid, yet object creation succeeded
        assert "not alphanumeric" in str(e)
        
    # The object can be serialized despite having an invalid title
    result = eb.to_dict()
    assert isinstance(result, dict)
    assert result["Type"] == "AWS::Events::EventBus"


if __name__ == "__main__":
    # Direct demonstration
    print("Demonstrating validation bypass bug:\n")
    
    for title in [None, ""]:
        print(f"Title: {title!r}")
        
        # Step 1: Create object (succeeds)
        eb = events.EventBus(title, Name='test-bus')
        print(f"  ✓ Object created successfully")
        
        # Step 2: Serialize (succeeds)
        result = eb.to_dict()
        print(f"  ✓ Serialized: {result}")
        
        # Step 3: But validation would fail
        try:
            eb.validate_title()
            print(f"  ✓ Validation passed")
        except ValueError as e:
            print(f"  ✗ Validation failed: {e}")
        
        print()