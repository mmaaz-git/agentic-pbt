import warnings
import sys
import gc
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import string
import pydantic
from pydantic import error_wrappers
from pydantic.errors import PydanticImportError
from pydantic._migration import getattr_migration
import threading
import time


@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=30))
def test_getattr_with_module_not_in_sys_modules(attr_name):
    """Test getattr_migration when module is not in sys.modules."""
    assume(not attr_name.startswith("__"))
    
    # Create a getattr function for a non-existent module
    fake_module = "pydantic.fake_module_that_does_not_exist"
    getattr_func = getattr_migration(fake_module)
    
    # This should handle the case gracefully
    try:
        result = getattr_func(attr_name)
        # If it succeeds, something weird happened
        assert False, f"Expected error for non-existent module, got {result}"
    except (AttributeError, KeyError, PydanticImportError) as e:
        # These are all acceptable errors
        pass
    except Exception as e:
        # Any other exception might be a bug
        assert False, f"Unexpected exception {type(e).__name__}: {e}"


@given(st.lists(st.sampled_from(["ValidationError", "ErrorWrapper"]), min_size=2, max_size=10))
def test_concurrent_attribute_access(attr_names):
    """Test thread safety of concurrent attribute access."""
    results = []
    errors = []
    
    def access_attribute(attr_name):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                obj = getattr(error_wrappers, attr_name)
                results.append((attr_name, "success", type(obj).__name__))
        except PydanticImportError as e:
            errors.append((attr_name, "import_error", str(e)))
        except AttributeError as e:
            errors.append((attr_name, "attr_error", str(e)))
    
    # Create threads
    threads = [threading.Thread(target=access_attribute, args=(name,)) 
               for name in attr_names]
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    # Should have results for all accesses
    assert len(results) + len(errors) == len(attr_names)


@given(st.just("ValidationError"))
def test_warning_state_isolation(attr_name):
    """Test that warning state changes don't leak between accesses."""
    # First access with warnings enabled
    with warnings.catch_warnings(record=True) as w1:
        warnings.simplefilter("always")
        obj1 = getattr(error_wrappers, attr_name)
        count1 = len(w1)
    
    # Second access with warnings disabled
    with warnings.catch_warnings(record=True) as w2:
        warnings.simplefilter("ignore")
        obj2 = getattr(error_wrappers, attr_name)
        count2 = len(w2)
    
    # Third access with warnings enabled again
    with warnings.catch_warnings(record=True) as w3:
        warnings.simplefilter("always")
        obj3 = getattr(error_wrappers, attr_name)
        count3 = len(w3)
    
    # First and third should have warnings, second shouldn't
    assert count1 == 1
    assert count2 == 0
    assert count3 == 1
    
    # All should return the same object
    assert obj1 is obj2 is obj3


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
def test_getattr_migration_with_invalid_import_paths(attr_name):
    """Test behavior when import_string would fail for moved attributes."""
    # Create a custom getattr function
    func = getattr_migration("pydantic.error_wrappers")
    
    # Directly test the wrapper function
    try:
        result = func(attr_name)
        # If it succeeds, it should be a valid attribute
    except (AttributeError, PydanticImportError):
        # Expected for non-existent or removed attributes
        pass
    except Exception as e:
        # Check if it's an import-related error that should be handled better
        error_type = type(e).__name__
        # ImportError and ModuleNotFoundError should be caught and re-raised as appropriate
        assert error_type not in ["ImportError", "ModuleNotFoundError"], \
            f"Unhandled {error_type} for attribute {attr_name}: {e}"


@given(st.sampled_from(["\x00", "None", "True", "False", "", " ", "\t", "\n"]))
def test_special_string_attribute_names(attr_name):
    """Test attribute access with special string values."""
    try:
        result = getattr(error_wrappers, attr_name)
        # Some of these might actually be valid attributes
        assert hasattr(error_wrappers, attr_name)
    except (AttributeError, PydanticImportError):
        # Expected for most special strings
        pass
    except Exception as e:
        # Should only get AttributeError or PydanticImportError
        assert False, f"Unexpected exception {type(e).__name__} for attribute '{repr(attr_name)}': {e}"


@given(st.integers(min_value=0, max_value=1000))
def test_numeric_string_attribute_names(number):
    """Test attribute access with numeric string names."""
    attr_name = str(number)
    
    try:
        result = getattr(error_wrappers, attr_name)
        # Numeric strings are not valid Python identifiers
        assert False, f"Should not be able to access attribute '{attr_name}'"
    except AttributeError as e:
        # This is expected
        assert "has no attribute" in str(e)
    except PydanticImportError:
        # This would be unexpected for numeric strings
        assert False, f"Unexpected PydanticImportError for numeric attribute '{attr_name}'"


@given(st.sampled_from(["__dict__", "__module__", "__name__", "__doc__", "__file__", "__package__"]))
def test_dunder_attribute_access(attr_name):
    """Test access to double-underscore attributes."""
    try:
        result = getattr(error_wrappers, attr_name)
        # These are standard module attributes and should work
        assert result is not None or attr_name == "__doc__"  # __doc__ can be None
    except AttributeError as e:
        # Some dunder attributes might not exist
        if attr_name == "__path__":
            # __path__ is specifically handled to raise AttributeError
            assert "has no attribute '__path__'" in str(e)
        else:
            # Other missing dunder attributes
            assert "has no attribute" in str(e)


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=200))
def test_long_attribute_names(attr_name):
    """Test attribute access with very long names."""
    try:
        result = getattr(error_wrappers, attr_name)
        # If it works, fine
    except (AttributeError, PydanticImportError):
        # Expected for non-existent attributes
        pass
    except RecursionError:
        # This would be a bug - long names shouldn't cause recursion
        assert False, f"RecursionError for long attribute name of length {len(attr_name)}"
    except MemoryError:
        # This would be a bug - reasonable length names shouldn't cause memory issues
        assert False, f"MemoryError for attribute name of length {len(attr_name)}"


@given(st.just("ValidationError"))
def test_moved_attribute_after_module_reload(attr_name):
    """Test that moved attributes work correctly after module reload."""
    import importlib
    
    # First access
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        obj1 = getattr(error_wrappers, attr_name)
    
    # Reload the module
    importlib.reload(error_wrappers)
    
    # Second access after reload
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        obj2 = getattr(error_wrappers, attr_name)
    
    # Should still work and return the same class
    assert type(obj1) == type(obj2)
    assert obj1.__name__ == obj2.__name__


@given(st.sampled_from(["ValidationError"]))
def test_getattr_vs_direct_import_consistency(attr_name):
    """Test that getattr and 'from ... import' give same results."""
    # Using getattr
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        obj_via_getattr = getattr(error_wrappers, attr_name)
    
    # Using from...import (dynamically)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        exec_globals = {}
        exec(f"from pydantic.error_wrappers import {attr_name}", exec_globals)
        obj_via_import = exec_globals[attr_name]
        
        # Should have warning for the import too
        assert len(w) == 1
        assert "has been moved" in str(w[0].message)
    
    # Should be the same object
    assert obj_via_getattr is obj_via_import