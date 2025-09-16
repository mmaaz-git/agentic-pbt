import warnings
import sys
from hypothesis import given, strategies as st, assume, settings
import string
import pydantic
from pydantic import error_wrappers
from pydantic.errors import PydanticImportError


@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=30))
def test_attribute_assignment_behavior(attr_name):
    """Test that attribute assignment behaves correctly on the migration module."""
    # Skip special Python attributes
    assume(not attr_name.startswith("__"))
    assume(attr_name not in ["ValidationError", "ErrorWrapper", "getattr_migration"])
    
    # Try to set an attribute
    original_value = object()
    try:
        setattr(error_wrappers, attr_name, original_value)
        # If successful, verify we can get it back
        retrieved = getattr(error_wrappers, attr_name)
        assert retrieved is original_value
        
        # Clean up
        delattr(error_wrappers, attr_name)
    except (AttributeError, TypeError) as e:
        # Some attributes might be read-only, which is fine
        pass


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=19).map(lambda s: "_" + s))
@settings(suppress_health_check=[])
def test_private_attribute_behavior(attr_name):
    """Test behavior with private (underscore-prefixed) attributes."""
    # attr_name is guaranteed to start with single underscore by construction
    assume(not attr_name.startswith("__"))
    
    try:
        result = getattr(error_wrappers, attr_name)
        # If it exists, it should not trigger migration warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            getattr(error_wrappers, attr_name)
            # Private attributes shouldn't trigger migration warnings
            migration_warnings = [warning for warning in w 
                                  if "has been moved" in str(warning.message)]
            assert len(migration_warnings) == 0
    except AttributeError:
        # This is expected for non-existent private attributes
        pass
    except PydanticImportError:
        # Private attributes shouldn't be in the migration mappings
        assert False, f"Unexpected PydanticImportError for private attribute {attr_name}"


@given(st.integers(min_value=1, max_value=10))
def test_multiple_warnings_for_moved_attribute(num_accesses):
    """Test that accessing a moved attribute multiple times generates multiple warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        for _ in range(num_accesses):
            getattr(error_wrappers, "ValidationError")
        
        # Should have one warning per access
        assert len(w) == num_accesses
        
        # All warnings should be identical
        first_msg = str(w[0].message)
        for warning in w:
            assert str(warning.message) == first_msg


@given(st.booleans())
def test_warning_filter_respected(should_filter):
    """Test that warning filters are properly respected."""
    with warnings.catch_warnings(record=True) as w:
        if should_filter:
            warnings.simplefilter("ignore")
        else:
            warnings.simplefilter("always")
        
        getattr(error_wrappers, "ValidationError")
        
        if should_filter:
            assert len(w) == 0
        else:
            assert len(w) == 1


@given(st.lists(st.sampled_from(["ValidationError", "ErrorWrapper", "getattr_migration", "NonExistent"]), 
                min_size=1, max_size=5))
def test_mixed_attribute_access_sequence(attr_names):
    """Test accessing a sequence of different attribute types."""
    results = []
    
    for attr_name in attr_names:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                obj = getattr(error_wrappers, attr_name)
                results.append((attr_name, "success", type(obj).__name__))
            except PydanticImportError:
                results.append((attr_name, "import_error", None))
            except AttributeError:
                results.append((attr_name, "attr_error", None))
    
    # Verify consistent behavior for each attribute
    for attr_name in set(attr_names):
        attr_results = [r for r in results if r[0] == attr_name]
        # All accesses to the same attribute should have the same result type
        result_types = [r[1] for r in attr_results]
        assert len(set(result_types)) == 1


@given(st.text(alphabet=string.printable.replace("\n", "").replace("\r", ""), 
               min_size=1, max_size=30))
def test_attribute_name_with_special_chars(attr_name):
    """Test attribute access with names containing special characters."""
    # Python identifiers have specific rules, so many will fail
    try:
        result = getattr(error_wrappers, attr_name)
        # If it succeeds, the name must be a valid Python identifier
        assert attr_name.isidentifier()
    except (AttributeError, PydanticImportError):
        # Expected for invalid identifiers or non-existent attributes
        pass
    except Exception as e:
        # Should only get AttributeError or PydanticImportError
        assert False, f"Unexpected exception {type(e).__name__} for attribute '{attr_name}'"


@given(st.just("ValidationError"))
def test_moved_attribute_identity_preservation(attr_name):
    """Test that moved attributes preserve identity across multiple accesses."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        # Get the attribute multiple times
        obj1 = getattr(error_wrappers, attr_name)
        obj2 = getattr(error_wrappers, attr_name)
        obj3 = getattr(pydantic, attr_name)
        
        # All should be the same object (identity, not just equality)
        assert obj1 is obj2
        assert obj2 is obj3
        assert obj1 is obj3


@given(st.sampled_from([
    ("ValidationError", "pydantic"),
]))
def test_circular_import_safety(attr_and_target):
    """Test that the migration doesn't cause circular import issues."""
    attr_name, expected_module = attr_and_target
    
    # Clear the module from sys.modules to force reimport
    modules_to_clear = [k for k in sys.modules.keys() 
                        if k.startswith('pydantic.error_wrappers')]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    # Re-import and access the moved attribute
    import pydantic.error_wrappers as ew
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        obj = getattr(ew, attr_name)
        
        # Should successfully import without circular dependency
        assert obj is not None


@given(st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
                min_size=0, max_size=5))
def test_dir_function_behavior(extra_attrs):
    """Test that dir() on the module returns expected attributes."""
    # Get the current dir() output
    current_dir = dir(error_wrappers)
    
    # Add some attributes
    for attr in extra_attrs:
        try:
            setattr(error_wrappers, attr, f"test_value_{attr}")
        except:
            continue
    
    # Get new dir() output
    new_dir = dir(error_wrappers)
    
    # Clean up
    for attr in extra_attrs:
        try:
            delattr(error_wrappers, attr)
        except:
            pass
    
    # dir() should include the standard attributes
    assert "getattr_migration" in current_dir
    assert "__name__" in current_dir
    assert "__file__" in current_dir