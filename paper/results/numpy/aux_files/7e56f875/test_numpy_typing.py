"""Property-based tests for numpy.typing module."""

import warnings
from hypothesis import given, strategies as st, assume
import numpy.typing as npt


@given(st.text())
def test_getattr_behavior(attr_name):
    """Test that __getattr__ has consistent behavior."""
    # This tests the invariant that:
    # 1. If attr is in __dir__(), getattr should succeed
    # 2. If attr is not in __dir__() and not "NBitBase", getattr should raise AttributeError
    # 3. The error message format should be consistent
    
    module_attrs = dir(npt)
    
    if attr_name in module_attrs:
        # Should not raise
        try:
            result = getattr(npt, attr_name)
            assert result is not None  # Should return something
        except AttributeError:
            # If it's in dir() but raises AttributeError, that's a bug
            assert False, f"Attribute {attr_name} is in dir() but raises AttributeError"
    elif attr_name == "NBitBase":
        # Special case: NBitBase should issue a deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = getattr(npt, attr_name)
            # Should have gotten a deprecation warning
            assert len(w) > 0
            assert issubclass(w[0].category, DeprecationWarning)
            assert "NBitBase" in str(w[0].message)
    else:
        # Should raise AttributeError with specific message format
        try:
            getattr(npt, attr_name)
            assert False, f"Expected AttributeError for {attr_name}"
        except AttributeError as e:
            error_msg = str(e)
            # Check the error message format matches expected pattern
            expected = f"module 'numpy.typing' has no attribute '{attr_name}'"
            assert error_msg == expected, f"Error message format mismatch: {error_msg}"


@given(st.sampled_from(["ArrayLike", "DTypeLike", "NBitBase", "NDArray"]))
def test_public_attributes_accessible(attr_name):
    """Test that all advertised public attributes are accessible."""
    # These are the public attributes according to __all__
    result = getattr(npt, attr_name)
    assert result is not None


@given(st.text())
def test_dir_consistency(attr_name):
    """Test that dir() results are consistent with actual attribute access."""
    # This property checks that if something is in dir(), we can get it
    module_dir = dir(npt)
    
    if attr_name in module_dir:
        # If it's in dir(), we should be able to access it
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # Ignore deprecation warnings for this test
                result = getattr(npt, attr_name)
                # Successfully accessed
        except AttributeError:
            # This would be a bug - dir() says it exists but getattr fails
            assert False, f"dir() contains {attr_name} but getattr() fails"


@given(st.text(min_size=1).filter(lambda x: not x.startswith('_')))
def test_nbitbase_subclass_restriction(class_name):
    """Test that NBitBase enforces subclass restrictions."""
    # NBitBase should only allow specific subclass names
    allowed_names = {"NBitBase", "_128Bit", "_96Bit", "_64Bit", "_32Bit", "_16Bit", "_8Bit"}
    
    if class_name not in allowed_names:
        # Should not be able to create arbitrary subclasses
        try:
            # Try to create a subclass with the given name
            type(class_name, (npt.NBitBase,), {})
            assert False, f"Should not be able to create subclass {class_name}"
        except TypeError as e:
            assert 'cannot inherit from final class "NBitBase"' in str(e)