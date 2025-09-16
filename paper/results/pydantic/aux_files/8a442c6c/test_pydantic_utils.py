"""Property-based tests for pydantic.utils.getattr_migration"""

import sys
import warnings
from hypothesis import given, strategies as st, assume, settings
import pydantic.utils
from pydantic.errors import PydanticImportError
from pydantic._migration import MOVED_IN_V2, DEPRECATED_MOVED_IN_V2, REDIRECT_TO_V1, REMOVED_IN_V2


# Test 1: AttributeError for '__path__' is always raised regardless of module name
@given(st.text(min_size=1))
def test_path_always_raises_attribute_error(module_name):
    """The function should always raise AttributeError for '__path__' attribute."""
    wrapper = pydantic.utils.getattr_migration(module_name)
    
    try:
        wrapper('__path__')
        assert False, "Should have raised AttributeError"
    except AttributeError as e:
        # Check that error message contains both module and attribute name
        error_msg = str(e)
        assert module_name in error_msg or repr(module_name) in error_msg
        assert '__path__' in error_msg or "'__path__'" in error_msg


# Test 2: Deterministic behavior - same input always produces same result/error
@given(st.text(min_size=1), st.text(min_size=1))
def test_deterministic_behavior(module_name, attr_name):
    """Multiple calls with same arguments should produce same result/error."""
    wrapper = pydantic.utils.getattr_migration(module_name)
    
    # First call
    result1 = None
    error1 = None
    try:
        result1 = wrapper(attr_name)
    except Exception as e:
        error1 = (type(e), str(e))
    
    # Second call
    result2 = None
    error2 = None
    try:
        result2 = wrapper(attr_name)
    except Exception as e:
        error2 = (type(e), str(e))
    
    # Results should be the same
    if error1:
        assert error2 is not None, "First call raised error but second didn't"
        assert error1[0] == error2[0], f"Different error types: {error1[0]} vs {error2[0]}"
        assert error1[1] == error2[1], f"Different error messages: {error1[1]} vs {error2[1]}"
    else:
        assert error2 is None, "First call succeeded but second raised error"
        assert result1 == result2, "Different results for same input"


# Test 3: Error message format for non-existent attributes
@given(st.text(min_size=1, max_size=100).filter(lambda x: '\\x00' not in x), 
       st.text(min_size=1, max_size=100).filter(lambda x: '\\x00' not in x and x != '__path__'))
def test_error_message_format(module_name, attr_name):
    """Error messages should have consistent format with proper quoting."""
    # Construct an import path that won't be in any of the migration dicts
    import_path = f"{module_name}:{attr_name}"
    
    # Skip if this happens to be a real migration path
    assume(import_path not in MOVED_IN_V2)
    assume(import_path not in DEPRECATED_MOVED_IN_V2)
    assume(import_path not in REDIRECT_TO_V1)
    assume(import_path not in REMOVED_IN_V2)
    assume(import_path != 'pydantic:BaseSettings')  # Special case
    
    # Also need to ensure the module doesn't exist in sys.modules
    # or the attribute doesn't exist if module does
    wrapper = pydantic.utils.getattr_migration(module_name)
    
    # Mock the module to ensure clean test
    if module_name in sys.modules:
        old_module = sys.modules[module_name]
        # Temporarily remove to test the error path
        del sys.modules[module_name]
    else:
        old_module = None
    
    try:
        wrapper(attr_name)
        assert False, "Should have raised AttributeError"
    except AttributeError as e:
        error_msg = str(e)
        # Check format: module 'X' has no attribute 'Y'
        assert 'module' in error_msg
        assert 'has no attribute' in error_msg
        # Check module and attribute are quoted
        assert repr(module_name) in error_msg or f"'{module_name}'" in error_msg
        assert repr(attr_name) in error_msg or f"'{attr_name}'" in error_msg
    except (ImportError, PydanticImportError):
        # These are valid errors for certain inputs
        pass
    finally:
        # Restore module if it existed
        if old_module is not None:
            sys.modules[module_name] = old_module


# Test 4: REMOVED_IN_V2 items always raise PydanticImportError
@given(st.sampled_from(list(REMOVED_IN_V2)))
def test_removed_items_raise_import_error(import_path):
    """Items in REMOVED_IN_V2 should always raise PydanticImportError."""
    module_name, attr_name = import_path.split(':')
    wrapper = pydantic.utils.getattr_migration(module_name)
    
    try:
        wrapper(attr_name)
        assert False, f"Should have raised PydanticImportError for {import_path}"
    except PydanticImportError as e:
        error_msg = str(e)
        assert import_path in error_msg
        assert 'has been removed in V2' in error_msg


# Test 5: MOVED_IN_V2 items raise warnings
@given(st.sampled_from(list(MOVED_IN_V2.items())))
@settings(max_examples=20)  # Limit because these do actual imports
def test_moved_items_raise_warnings(item):
    """Items in MOVED_IN_V2 should raise deprecation warnings."""
    import_path, new_location = item
    module_name, attr_name = import_path.split(':')
    wrapper = pydantic.utils.getattr_migration(module_name)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            result = wrapper(attr_name)
            # Should have raised a warning
            assert len(w) > 0, f"No warning raised for moved item {import_path}"
            warning_msg = str(w[0].message)
            assert import_path in warning_msg
            assert new_location in warning_msg
            assert 'has been moved to' in warning_msg
        except (ImportError, AttributeError, PydanticImportError):
            # Some items might not be importable in test environment
            pass


# Test 6: Special case for BaseSettings
def test_base_settings_special_case():
    """BaseSettings should raise a specific PydanticImportError."""
    wrapper = pydantic.utils.getattr_migration('pydantic')
    
    try:
        wrapper('BaseSettings')
        assert False, "Should have raised PydanticImportError"
    except PydanticImportError as e:
        error_msg = str(e)
        assert 'BaseSettings' in error_msg
        assert 'pydantic-settings' in error_msg
        assert 'has been moved to' in error_msg


# Test 7: Idempotence for error-raising paths
@given(st.text(min_size=1, max_size=50), st.integers(min_value=2, max_value=5))
def test_error_idempotence(module_name, num_calls):
    """Calling wrapper multiple times with error-inducing input should raise same error."""
    wrapper = pydantic.utils.getattr_migration(module_name)
    
    errors = []
    for _ in range(num_calls):
        try:
            wrapper('__path__')
        except AttributeError as e:
            errors.append(str(e))
    
    # All errors should be identical
    assert len(errors) == num_calls
    assert all(e == errors[0] for e in errors)


# Test 8: Module name handling with special characters
@given(st.text(alphabet=st.characters(blacklist_categories=['Cs', 'Cc']), min_size=1, max_size=50))
def test_module_name_with_special_chars(module_name):
    """Module names with special characters should be properly quoted in errors."""
    wrapper = pydantic.utils.getattr_migration(module_name)
    
    try:
        wrapper('__path__')
    except AttributeError as e:
        error_msg = str(e)
        # Module name should be properly represented in the error
        assert repr(module_name) in error_msg or module_name in error_msg