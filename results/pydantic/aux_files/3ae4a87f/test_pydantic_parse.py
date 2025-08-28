"""Property-based tests for pydantic.parse module using Hypothesis."""

import warnings
from hypothesis import given, strategies as st, assume
import pytest
import sys
import re

# Import the modules we're testing
import pydantic.parse
import pydantic._migration as migration
from pydantic.errors import PydanticImportError


# Test 1: __path__ always raises AttributeError
@given(st.just("__path__"))
def test_getattr_migration_path_attribute(attr_name):
    """Test that __path__ always raises AttributeError as documented."""
    wrapper = migration.getattr_migration('pydantic.parse')
    with pytest.raises(AttributeError, match=r"module 'pydantic.parse' has no attribute '__path__'"):
        wrapper(attr_name)


# Test 2: MOVED_IN_V2 items should emit warnings and return the correct object
@given(st.sampled_from(list(migration.MOVED_IN_V2.keys())))
def test_getattr_migration_moved_items(import_path):
    """Test that moved items emit warnings and return the correct object."""
    # Only test items that are from pydantic module
    assume(import_path.startswith('pydantic'))
    
    module_name, attr_name = import_path.split(':', 1)
    wrapper = migration.getattr_migration(module_name)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = wrapper(attr_name)
        
        # Should have gotten a warning
        assert len(w) >= 1, f"No warning emitted for moved item {import_path}"
        warning_messages = [str(warning.message) for warning in w]
        assert any(f"`{import_path}` has been moved" in msg for msg in warning_messages), \
            f"Expected move warning for {import_path}, got: {warning_messages}"
        
        # Result should not be None (should be the actual moved object)
        assert result is not None, f"Got None for moved item {import_path}"


# Test 3: REMOVED_IN_V2 items should raise PydanticImportError
@given(st.sampled_from(list(migration.REMOVED_IN_V2)))
def test_getattr_migration_removed_items(import_path):
    """Test that removed items raise PydanticImportError."""
    # Only test items that are from pydantic module
    assume(':' in import_path and import_path.startswith('pydantic'))
    
    module_name, attr_name = import_path.split(':', 1)
    wrapper = migration.getattr_migration(module_name)
    
    with pytest.raises(PydanticImportError, match=f"`{re.escape(import_path)}` has been removed"):
        wrapper(attr_name)


# Test 4: Non-existent attributes should raise AttributeError
@given(st.text(min_size=1, max_size=50).filter(
    lambda s: s not in ['__path__'] and 
              not s.startswith('_') and 
              s.isidentifier() and
              f'pydantic.parse:{s}' not in migration.MOVED_IN_V2 and
              f'pydantic.parse:{s}' not in migration.REMOVED_IN_V2 and
              f'pydantic.parse:{s}' not in migration.REDIRECT_TO_V1 and
              f'pydantic.parse:{s}' not in migration.DEPRECATED_MOVED_IN_V2
))
def test_getattr_migration_nonexistent_attributes(attr_name):
    """Test that non-existent attributes raise AttributeError."""
    wrapper = migration.getattr_migration('pydantic.parse')
    
    # Check if the attribute exists in the module's globals
    if hasattr(pydantic.parse, attr_name):
        # If it exists, it should return without error
        result = wrapper(attr_name)
        assert result is not None
    else:
        # If it doesn't exist, should raise AttributeError
        with pytest.raises(AttributeError, match=f"module 'pydantic.parse' has no attribute"):
            wrapper(attr_name)


# Test 5: Idempotence - calling wrapper multiple times with same input gives same result
@given(st.sampled_from(['__path__', 'getattr_migration', 'nonexistent_attr_xyz']))
def test_getattr_migration_idempotence(attr_name):
    """Test that calling wrapper multiple times with same input behaves consistently."""
    wrapper = migration.getattr_migration('pydantic.parse')
    
    # Try calling twice and compare behavior
    error1 = None
    result1 = None
    try:
        result1 = wrapper(attr_name)
    except Exception as e:
        error1 = type(e)
    
    error2 = None
    result2 = None
    try:
        result2 = wrapper(attr_name)
    except Exception as e:
        error2 = type(e)
    
    # Both calls should have same behavior
    assert error1 == error2, f"Different errors for {attr_name}: {error1} vs {error2}"
    if error1 is None:
        assert result1 == result2, f"Different results for {attr_name}"


# Test 6: REDIRECT_TO_V1 items should emit warnings
@given(st.sampled_from(list(migration.REDIRECT_TO_V1.keys())))
def test_getattr_migration_redirect_v1(import_path):
    """Test that V1 redirect items emit proper warnings."""
    assume(import_path.startswith('pydantic'))
    
    module_name, attr_name = import_path.split(':', 1)
    wrapper = migration.getattr_migration(module_name)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = wrapper(attr_name)
        
        # Should have gotten a warning about redirection
        assert len(w) >= 1, f"No warning emitted for V1 redirect {import_path}"
        warning_messages = [str(warning.message) for warning in w]
        assert any("has been removed" in msg and "importing from" in msg 
                  for msg in warning_messages), \
            f"Expected redirect warning for {import_path}, got: {warning_messages}"
        
        # Result should not be None
        assert result is not None, f"Got None for V1 redirect {import_path}"


# Test 7: BaseSettings special case
def test_getattr_migration_base_settings():
    """Test that BaseSettings raises a specific PydanticImportError."""
    wrapper = migration.getattr_migration('pydantic')
    
    with pytest.raises(PydanticImportError) as exc_info:
        wrapper('BaseSettings')
    
    assert 'pydantic-settings' in str(exc_info.value)
    assert 'has been moved' in str(exc_info.value)