"""Property-based test that discovers the empty title validation bug."""

from hypothesis import given, strategies as st
from troposphere import shield
import pytest


@given(title=st.one_of(st.none(), st.text(max_size=10)))
def test_title_validation_consistency(title):
    """Test that title validation is consistent between __init__ and validate_title()."""
    
    # Try to create an object
    try:
        obj = shield.DRTAccess(title, RoleArn='arn:aws:iam::123456789012:role/Test')
        created = True
        creation_error = None
    except (ValueError, TypeError) as e:
        created = False
        creation_error = e
    
    if created:
        # If creation succeeded, validate_title should also succeed
        try:
            obj.validate_title()
            validation_passed = True
            validation_error = None
        except ValueError as e:
            validation_passed = False
            validation_error = e
        
        # PROPERTY: If __init__ accepts a title, validate_title() should too
        assert validation_passed, (
            f"Inconsistent validation: __init__ accepted title {repr(title)} "
            f"but validate_title() rejected it with: {validation_error}"
        )
    
    # Also test the reverse: if validate_title rejects, __init__ should too
    # (This is already implicitly tested above)


if __name__ == '__main__':
    # Run the test
    test_title_validation_consistency()