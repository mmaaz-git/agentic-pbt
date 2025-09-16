"""Test for potential bug in fetch method parameter handling."""

from hypothesis import given, strategies as st
from sqlalchemy.future import select
from sqlalchemy import column
import warnings


# Test the warning issue with fetch
@given(st.integers(min_value=0, max_value=100), st.integers(min_value=0, max_value=100))
def test_fetch_invalid_parameter_warning(count, offset_val):
    """Test that fetch with invalid parameter 'with_offset' produces a warning."""
    s = select(column('x'))
    
    # This should trigger a warning about invalid parameter
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        s_fetch = s.fetch(count, with_offset=offset_val)
        
        # Check if warning was raised
        assert len(w) > 0
        assert "Can't validate argument 'with_offset'" in str(w[0].message)
        
        # Despite the warning, the operation should still work
        assert s_fetch is not None
        assert s_fetch is not s


@given(st.integers(min_value=0, max_value=100))
def test_fetch_with_correct_parameters(count):
    """Test fetch with correct parameters."""
    s = select(column('x'))
    
    # Use correct parameters
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        s_fetch = s.fetch(count, with_ties=False, percent=False)
        
        # Should not produce warnings
        assert len(w) == 0
        assert s_fetch is not None
        assert s_fetch is not s


def test_fetch_accepts_arbitrary_kwargs():
    """Test that fetch accepts arbitrary keyword arguments without validation."""
    s = select(column('x'))
    
    # Try various invalid parameters
    invalid_params = [
        {'invalid_param': 123},
        {'another_bad': 'test'},
        {'with_offset': 10},  # This looks like it should work but doesn't
        {'random_dialect_kw': True}
    ]
    
    for params in invalid_params:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s_fetch = s.fetch(10, **params)
            
            # Check for warnings
            if w:
                warning_messages = [str(warning.message) for warning in w]
                print(f"Params {params} produced warnings: {warning_messages}")
            
            # Despite warnings, should still create object
            assert s_fetch is not None
            assert s_fetch is not s


if __name__ == "__main__":
    test_fetch_accepts_arbitrary_kwargs()
    print("\nAll manual tests completed.")