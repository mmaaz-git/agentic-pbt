"""Property-based tests for pydantic.validators and its migration function."""

import warnings
from hypothesis import given, strategies as st, assume, settings
import string
import re

from pydantic._migration import (
    getattr_migration,
    MOVED_IN_V2,
    DEPRECATED_MOVED_IN_V2,
    REDIRECT_TO_V1,
    REMOVED_IN_V2
)
from pydantic._internal._validators import import_string
from pydantic.errors import PydanticImportError


# Property 1: Import consistency - moved items should return same object as direct import
@given(st.sampled_from(list(MOVED_IN_V2.items())))
def test_moved_items_import_consistency(item):
    """Moved items accessed via migration should return same object as direct import."""
    old_path, new_path = item
    module, name = old_path.split(':')
    
    # Get wrapper for the module
    wrapper = getattr_migration(module)
    
    # Access via migration wrapper
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        migrated_obj = wrapper(name)
    
    # Direct import
    direct_obj = import_string(new_path)
    
    # They should be the same object
    assert migrated_obj is direct_obj, f"Migration for {old_path} doesn't return same object as {new_path}"


# Property 2: Warning generation for moved items
@given(st.sampled_from(list(MOVED_IN_V2.items())))
def test_moved_items_generate_warnings(item):
    """Accessing moved items should generate appropriate warning messages."""
    old_path, new_path = item
    module, name = old_path.split(':')
    
    wrapper = getattr_migration(module)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        wrapper(name)
        
        # Should have generated a warning
        assert len(w) >= 1, f"No warning generated for moved item {old_path}"
        
        # Warning message should mention both old and new locations
        warning_msg = str(w[0].message)
        assert old_path in warning_msg, f"Warning doesn't mention old path {old_path}"
        assert new_path in warning_msg, f"Warning doesn't mention new path {new_path}"


# Property 3: Removed items should raise PydanticImportError
@given(st.sampled_from(list(REMOVED_IN_V2)))
def test_removed_items_raise_error(removed_path):
    """Removed items should raise PydanticImportError with appropriate message."""
    if ':' not in removed_path:
        return  # Skip if not in module:name format
    
    module, name = removed_path.split(':', 1)
    wrapper = getattr_migration(module)
    
    try:
        wrapper(name)
        assert False, f"Expected PydanticImportError for {removed_path}"
    except PydanticImportError as e:
        # Error message should mention the removed path
        assert removed_path in str(e), f"Error doesn't mention {removed_path}"
        assert "removed" in str(e).lower(), "Error doesn't indicate removal"


# Property 4: Non-existent attributes should raise AttributeError
@given(
    st.text(
        alphabet=string.ascii_letters + string.digits + "_",
        min_size=1,
        max_size=50
    ).filter(lambda s: not s.startswith('_') and s.isidentifier())
)
def test_nonexistent_attributes_raise_attribute_error(name):
    """Non-existent attributes should raise AttributeError."""
    # Create test paths that shouldn't exist in any migration dictionary
    test_module = "pydantic.test_module_xyz"
    test_path = f"{test_module}:{name}"
    
    # Ensure this path doesn't exist in any migration dict
    assume(test_path not in MOVED_IN_V2)
    assume(test_path not in DEPRECATED_MOVED_IN_V2)
    assume(test_path not in REDIRECT_TO_V1)
    assume(test_path not in REMOVED_IN_V2)
    assume(name != '__path__')  # Special case in the code
    
    wrapper = getattr_migration(test_module)
    
    try:
        wrapper(name)
        assert False, f"Expected AttributeError for non-existent {name}"
    except AttributeError as e:
        # Should mention the module and attribute
        assert test_module in str(e), f"Error doesn't mention module {test_module}"
        assert name in str(e), f"Error doesn't mention attribute {name}"
    except Exception as e:
        assert False, f"Expected AttributeError but got {type(e).__name__}: {e}"


# Property 5: Import path construction and parsing
@given(
    st.text(
        alphabet=string.ascii_letters + "._",
        min_size=1,
        max_size=30
    ).filter(lambda s: '.' in s and not s.startswith('.') and not s.endswith('.')),
    st.text(
        alphabet=string.ascii_letters + string.digits + "_",
        min_size=1,
        max_size=30
    ).filter(lambda s: s.isidentifier() and not s.startswith('_'))
)
def test_import_path_construction(module, name):
    """Import path should be correctly constructed as module:name."""
    wrapper = getattr_migration(module)
    
    # The wrapper should construct path as module:name internally
    # We can verify this by checking error messages for non-existent attrs
    expected_path = f"{module}:{name}"
    
    # Assume this combination doesn't exist
    assume(expected_path not in MOVED_IN_V2)
    assume(expected_path not in DEPRECATED_MOVED_IN_V2)
    assume(expected_path not in REDIRECT_TO_V1)
    assume(expected_path not in REMOVED_IN_V2)
    assume(name != '__path__')
    
    try:
        wrapper(name)
    except (AttributeError, PydanticImportError):
        pass  # Expected
    except Exception as e:
        # Unexpected error type might indicate path construction issue
        assert False, f"Unexpected error for {expected_path}: {type(e).__name__}: {e}"


# Property 6: Special __path__ handling
@given(st.text(min_size=1, max_size=50))
def test_special_path_attribute(module_name):
    """__path__ attribute should always raise AttributeError."""
    wrapper = getattr_migration(module_name)
    
    try:
        wrapper('__path__')
        assert False, "Expected AttributeError for __path__"
    except AttributeError as e:
        assert module_name in str(e), f"Error doesn't mention module {module_name}"
        assert '__path__' in str(e), "Error doesn't mention __path__"


# Property 7: Redirect to V1 items should generate specific warning
@given(st.sampled_from(list(REDIRECT_TO_V1.items())))
def test_redirect_v1_warning_content(item):
    """Items redirected to V1 should generate warning with migration guide link."""
    old_path, new_path = item
    module, name = old_path.split(':')
    
    wrapper = getattr_migration(module)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            wrapper(name)
        except:
            pass  # Some might fail to import, we're testing warning generation
        
        if w:  # If warning was generated
            warning_msg = str(w[0].message)
            # Should mention removal and migration guide
            assert "removed" in warning_msg.lower(), "Warning doesn't mention removal"
            assert "migration" in warning_msg, "Warning doesn't mention migration guide"
            assert new_path in warning_msg, f"Warning doesn't mention redirect target {new_path}"


# Property 8: Deprecated moved items should not generate deprecation warning in wrapper
@given(st.sampled_from(list(DEPRECATED_MOVED_IN_V2.items())))  
def test_deprecated_moved_no_warning_in_wrapper(item):
    """Deprecated moved items should import successfully without warning in wrapper."""
    old_path, new_path = item
    module, name = old_path.split(':')
    
    wrapper = getattr_migration(module)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            obj = wrapper(name)
            # The wrapper itself shouldn't generate warnings for deprecated items
            # (deprecation warning comes from the actual usage)
            wrapper_warnings = [warning for warning in w 
                              if 'has been moved' in str(warning.message)]
            assert len(wrapper_warnings) == 0, f"Wrapper generated move warning for deprecated item {old_path}"
        except ImportError:
            pass  # Some deprecated items might not be importable in test env