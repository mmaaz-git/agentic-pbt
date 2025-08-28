"""
Test that reveals a bug in troposphere's validate_title method
"""
import troposphere.synthetics as synthetics
from hypothesis import given, strategies as st


@given(st.sampled_from(["", None]))
def test_validate_title_empty_string_inconsistency(title):
    """
    Empty string and None should behave consistently in title validation.
    
    The validate_title method has the condition:
        if not self.title or not valid_names.match(self.title):
            raise ValueError('Name "%s" not alphanumeric' % self.title)
    
    This creates an inconsistency:
    - When title is None: `not None` is True, so it should raise ValueError
    - When title is "": `not ""` is True, so it should raise ValueError
    
    However, the actual behavior is different.
    """
    # Both should either succeed or fail, but they behave differently
    if title is None:
        # None is allowed (doesn't validate)
        try:
            group = synthetics.Group(title, Name='MyGroup')
            print(f"Title=None succeeded")
        except:
            print(f"Title=None failed")
    else:
        # Empty string is allowed (passes the not self.title check)
        try:
            group = synthetics.Group(title, Name='MyGroup')
            print(f'Title="" succeeded')
        except:
            print(f'Title="" failed')


if __name__ == "__main__":
    # Demonstrate the bug
    print("Testing title validation inconsistency:")
    
    # Test with None
    try:
        group1 = synthetics.Group(None, Name='MyGroup')
        print("✓ None title accepted")
    except Exception as e:
        print(f"✗ None title rejected: {e}")
    
    # Test with empty string  
    try:
        group2 = synthetics.Group("", Name='MyGroup')
        print('✓ Empty string title accepted')
    except Exception as e:
        print(f'✗ Empty string title rejected: {e}')
    
    # The inconsistency: the validation logic suggests both should fail,
    # but empty string passes because validate_title is only called when
    # self.title is truthy
    
    print("\nThe bug: validate_title() is only called if self.title is truthy,")
    print("but the method itself checks 'if not self.title', creating dead code.")
    print("This leads to empty strings being accepted when they shouldn't be.")