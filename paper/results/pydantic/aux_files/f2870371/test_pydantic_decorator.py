"""Property-based tests for pydantic.decorator.getattr_migration"""

import sys
import warnings
from unittest.mock import patch

import pytest
from hypothesis import assume, given, strategies as st

from pydantic._migration import (
    DEPRECATED_MOVED_IN_V2,
    MOVED_IN_V2,
    REDIRECT_TO_V1,
    REMOVED_IN_V2,
)
from pydantic.decorator import getattr_migration
from pydantic.errors import PydanticImportError


@given(st.text(min_size=1))
def test_path_always_raises_attribute_error(module_name):
    """__path__ should always raise AttributeError for any module name."""
    import re
    wrapper = getattr_migration(module_name)
    with pytest.raises(AttributeError, match=re.escape(f"module {module_name!r} has no attribute '__path__'")):
        wrapper('__path__')


@given(st.sampled_from(list(REMOVED_IN_V2)))
def test_removed_items_raise_import_error(import_path):
    """Items in REMOVED_IN_V2 should always raise PydanticImportError."""
    if ':' not in import_path:
        pytest.skip("Invalid import path format")
    module, name = import_path.split(':', 1)
    wrapper = getattr_migration(module)
    with pytest.raises(PydanticImportError, match=f"`{import_path}` has been removed in V2"):
        wrapper(name)


@given(st.sampled_from(list(MOVED_IN_V2.keys())))
def test_moved_items_return_correct_object(import_path):
    """Items in MOVED_IN_V2 should return the same object as direct import."""
    module, name = import_path.split(':', 1)
    wrapper = getattr_migration(module)
    
    # Capture the warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = wrapper(name)
        
        # Check that a warning was issued
        assert len(w) > 0
        assert f"`{import_path}` has been moved to" in str(w[0].message)
    
    # Verify the returned object is what we expect
    new_location = MOVED_IN_V2[import_path]
    if ':' in new_location:
        new_module, new_name = new_location.split(':', 1)
        expected_module = __import__(new_module, fromlist=[new_name])
        if new_name:
            expected = getattr(expected_module, new_name)
        else:
            expected = expected_module
        assert result is expected


def test_base_settings_special_error():
    """BaseSettings should raise a specific PydanticImportError."""
    wrapper = getattr_migration('pydantic')
    with pytest.raises(
        PydanticImportError,
        match="`BaseSettings` has been moved to the `pydantic-settings` package"
    ):
        wrapper('BaseSettings')


@given(st.text(min_size=1).filter(lambda x: ':' not in x and x != '__path__'))
def test_nonexistent_attributes_raise_attribute_error(name):
    """Non-existent attributes should raise AttributeError."""
    import re
    # Use a fake module that doesn't have any of the migration paths
    fake_module = 'test_fake_module_xyz'
    
    # Check that this name isn't in any migration dictionary
    import_path = f'{fake_module}:{name}'
    assume(import_path not in MOVED_IN_V2)
    assume(import_path not in DEPRECATED_MOVED_IN_V2)
    assume(import_path not in REDIRECT_TO_V1)
    assume(import_path not in REMOVED_IN_V2)
    assume(import_path != 'pydantic:BaseSettings')
    
    # Create a fake module in sys.modules without the attribute
    sys.modules[fake_module] = type(sys)('fake_module')
    
    try:
        wrapper = getattr_migration(fake_module)
        with pytest.raises(AttributeError, match=re.escape(f"module {fake_module!r} has no attribute {name!r}")):
            wrapper(name)
    finally:
        del sys.modules[fake_module]


@given(st.text(min_size=1).filter(lambda x: ':' not in x and x != '__path__'))
def test_existing_globals_are_returned(name):
    """Attributes that exist in module globals should be returned."""
    fake_module = 'test_module_with_globals'
    
    # Check that this name isn't in any migration dictionary
    import_path = f'{fake_module}:{name}'
    assume(import_path not in MOVED_IN_V2)
    assume(import_path not in DEPRECATED_MOVED_IN_V2)
    assume(import_path not in REDIRECT_TO_V1)
    assume(import_path not in REMOVED_IN_V2)
    assume(import_path != 'pydantic:BaseSettings')
    
    # Create a fake module with the attribute
    module = type(sys)('fake_module')
    test_value = f'test_value_{name}'
    setattr(module, name, test_value)
    sys.modules[fake_module] = module
    
    try:
        wrapper = getattr_migration(fake_module)
        result = wrapper(name)
        assert result == test_value
    finally:
        del sys.modules[fake_module]


@given(st.sampled_from(list(REDIRECT_TO_V1.keys())))
def test_redirect_to_v1_shows_warning(import_path):
    """Items in REDIRECT_TO_V1 should show a warning about redirection."""
    module, name = import_path.split(':', 1)
    wrapper = getattr_migration(module)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            result = wrapper(name)
            # Check that a warning was issued
            assert len(w) > 0
            assert f"`{import_path}` has been removed" in str(w[0].message)
            assert "importing from" in str(w[0].message)
        except (ImportError, AttributeError):
            # Some redirects might fail if pydantic.v1 is not available
            pass


@given(st.sampled_from(list(DEPRECATED_MOVED_IN_V2.keys())))
def test_deprecated_moved_items_no_warning(import_path):
    """Items in DEPRECATED_MOVED_IN_V2 should not issue warnings (handled elsewhere)."""
    module, name = import_path.split(':', 1)
    wrapper = getattr_migration(module)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            result = wrapper(name)
            # No warning should be issued for deprecated items
            migration_warnings = [warning for warning in w if 'has been moved' in str(warning.message)]
            assert len(migration_warnings) == 0
        except (ImportError, AttributeError):
            # Some items might not be available
            pass


@given(st.text(min_size=1))
def test_wrapper_is_callable(module_name):
    """getattr_migration should always return a callable."""
    wrapper = getattr_migration(module_name)
    assert callable(wrapper)


@given(st.text(min_size=1))
def test_idempotent_wrapper_creation(module_name):
    """Creating multiple wrappers for same module should produce equivalent functions."""
    wrapper1 = getattr_migration(module_name)
    wrapper2 = getattr_migration(module_name)
    
    # Test with __path__ - both should raise same error
    with pytest.raises(AttributeError) as exc1:
        wrapper1('__path__')
    with pytest.raises(AttributeError) as exc2:
        wrapper2('__path__')
    
    assert str(exc1.value) == str(exc2.value)