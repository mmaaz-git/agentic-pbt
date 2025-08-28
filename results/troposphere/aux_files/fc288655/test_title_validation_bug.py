"""Test demonstrating title validation bug in troposphere"""

from hypothesis import given, strategies as st
import troposphere.events as events


@given(st.sampled_from([None, "", " ", "\t", "\n"]))
def test_title_validation_inconsistency(title):
    """
    Test that demonstrates inconsistent title validation.
    
    The validate_title() method checks: if not self.title or not valid_names.match(self.title)
    This suggests empty/None titles should be invalid.
    
    However, __init__ only calls validate_title() if self.title is truthy,
    allowing empty/None titles to bypass validation entirely.
    """
    # These should raise ValueError according to validate_title logic
    # but they don't because validation is skipped
    eb = events.EventBus(title, Name='test')
    
    # If we explicitly call validate_title, it should fail
    try:
        eb.validate_title()
        # If validation passes, the title must be valid
        assert title and title.strip() and title.isalnum()
    except ValueError:
        # This is expected for invalid titles
        pass
    
    # The bug: object creation succeeds but explicit validation would fail
    # This violates the contract that titles should be alphanumeric


if __name__ == "__main__":
    # Demonstrate the bug directly
    print("Demonstrating title validation bug:")
    
    test_titles = [None, "", " "]
    
    for title in test_titles:
        print(f"\nTesting title={title!r}")
        
        # Create object - this succeeds
        eb = events.EventBus(title, Name='test')
        print(f"  Object creation: SUCCESS")
        
        # But explicit validation fails
        try:
            eb.validate_title()
            print(f"  Explicit validation: SUCCESS")
        except ValueError as e:
            print(f"  Explicit validation: FAILED - {e}")
        
        # This is inconsistent behavior!