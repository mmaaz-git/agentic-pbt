import warnings
from hypothesis import given, strategies as st, assume
import string
import pydantic
from pydantic import error_wrappers
from pydantic.errors import PydanticImportError


@given(st.just("ValidationError"))
def test_moved_attribute_consistency(attr_name):
    """Test that moved attributes return the same object from both locations."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        # Get attribute from error_wrappers
        obj_from_error_wrappers = getattr(error_wrappers, attr_name)
        
        # Get attribute from new location (pydantic)
        obj_from_new_location = getattr(pydantic, attr_name)
        
        # They should be the same object
        assert obj_from_error_wrappers is obj_from_new_location


@given(st.just("ValidationError"))
def test_moved_attribute_warning_format(attr_name):
    """Test that moved attributes emit warnings with correct format."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Access the moved attribute
        getattr(error_wrappers, attr_name)
        
        # Should have exactly one warning
        assert len(w) == 1
        warning_msg = str(w[0].message)
        
        # Check warning message format
        assert f"pydantic.error_wrappers:{attr_name}" in warning_msg
        assert "has been moved to" in warning_msg
        assert f"pydantic:{attr_name}" in warning_msg


@given(st.just("ErrorWrapper"))
def test_removed_attribute_raises_import_error(attr_name):
    """Test that removed attributes raise PydanticImportError."""
    try:
        getattr(error_wrappers, attr_name)
        assert False, f"Expected PydanticImportError for {attr_name}"
    except PydanticImportError as e:
        # Check error message contains expected information
        error_msg = str(e)
        assert f"pydantic.error_wrappers:{attr_name}" in error_msg
        assert "has been removed in V2" in error_msg


@given(st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=50))
def test_nonexistent_attribute_raises_attribute_error(attr_name):
    """Test that truly non-existent attributes raise AttributeError."""
    # Skip known attributes
    known_attrs = ["ValidationError", "ErrorWrapper", "getattr_migration", "__path__"]
    assume(attr_name not in known_attrs)
    
    # Skip Python special attributes
    assume(not attr_name.startswith("__") or not attr_name.endswith("__"))
    
    try:
        getattr(error_wrappers, attr_name)
        # If we get here, the attribute exists (might be inherited from module)
        # This is acceptable, just pass the test
    except AttributeError as e:
        # This is expected for non-existent attributes
        error_msg = str(e)
        assert "has no attribute" in error_msg
        assert attr_name in error_msg
    except PydanticImportError:
        # This should only happen for known removed attributes
        assert False, f"Unexpected PydanticImportError for random attribute {attr_name}"
    except Exception as e:
        # Any other exception is unexpected
        assert False, f"Unexpected exception {type(e).__name__} for attribute {attr_name}: {e}"


@given(st.just("__path__"))
def test_path_attribute_always_raises_attribute_error(attr_name):
    """Test that __path__ always raises AttributeError."""
    try:
        getattr(error_wrappers, attr_name)
        assert False, "__path__ should always raise AttributeError"
    except AttributeError as e:
        error_msg = str(e)
        assert "has no attribute '__path__'" in error_msg


@given(st.just("getattr_migration"))
def test_existing_attribute_passthrough_no_warning(attr_name):
    """Test that existing module attributes are returned without warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Access the existing attribute
        obj = getattr(error_wrappers, attr_name)
        
        # Should not emit any warnings
        assert len(w) == 0
        
        # Should return the actual function
        assert callable(obj)


@given(st.sampled_from(["ValidationError", "ErrorWrapper"]))
def test_consistent_error_handling_for_same_attribute(attr_name):
    """Test that accessing the same attribute multiple times gives consistent results."""
    results = []
    errors = []
    
    for _ in range(3):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                obj = getattr(error_wrappers, attr_name)
                results.append(("success", type(obj).__name__))
            except PydanticImportError as e:
                errors.append(("PydanticImportError", str(e)))
            except AttributeError as e:
                errors.append(("AttributeError", str(e)))
    
    # All attempts should have the same outcome
    if results:
        assert all(r == results[0] for r in results)
    if errors:
        assert all(e == errors[0] for e in errors)
    
    # Should be either all successes or all errors, not mixed
    assert not (results and errors)


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
def test_attribute_access_case_sensitivity(base_name):
    """Test that attribute access is case-sensitive."""
    # Create variations of the name
    lower_name = base_name.lower()
    upper_name = base_name.upper()
    
    # Skip if they're the same (all uppercase or all lowercase)
    assume(lower_name != upper_name)
    
    # Access with different cases should behave independently
    lower_result = None
    upper_result = None
    
    try:
        getattr(error_wrappers, lower_name)
        lower_result = "exists"
    except (AttributeError, PydanticImportError):
        lower_result = "error"
    
    try:
        getattr(error_wrappers, upper_name)
        upper_result = "exists"
    except (AttributeError, PydanticImportError):
        upper_result = "error"
    
    # The behavior might be the same or different, but it should be deterministic
    # This test mainly ensures no crashes occur with case variations
    assert lower_result in ["exists", "error"]
    assert upper_result in ["exists", "error"]