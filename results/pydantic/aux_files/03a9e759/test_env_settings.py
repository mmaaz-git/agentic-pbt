import sys
import warnings
from hypothesis import given, strategies as st, assume
import pydantic.env_settings
from pydantic.errors import PydanticImportError
from pydantic._migration import getattr_migration


@given(st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith('_')))
def test_consistent_attribute_access(attr_name):
    """Property: Accessing the same attribute multiple times should behave identically."""
    assume(attr_name != '__path__')  # Special case in the code
    
    # First access
    first_error = None
    first_result = None
    first_warnings = []
    
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            first_result = getattr(pydantic.env_settings, attr_name)
            first_warnings = [str(warning.message) for warning in w]
    except Exception as e:
        first_error = (type(e), str(e))
    
    # Second access
    second_error = None
    second_result = None
    second_warnings = []
    
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            second_result = getattr(pydantic.env_settings, attr_name)
            second_warnings = [str(warning.message) for warning in w]
    except Exception as e:
        second_error = (type(e), str(e))
    
    # They should behave identically
    assert first_error == second_error
    if first_error is None:
        assert first_result == second_result
        assert first_warnings == second_warnings


def test_basesettings_special_case_inconsistency():
    """
    Test that BaseSettings special error handling is inconsistent.
    
    The code has a special check for 'pydantic:BaseSettings' but when accessed
    through pydantic.env_settings, the import_path is 'pydantic.env_settings:BaseSettings'.
    """
    # Access BaseSettings through pydantic module
    pydantic_error = None
    try:
        import pydantic
        _ = pydantic.BaseSettings
    except PydanticImportError as e:
        pydantic_error = str(e)
    
    # Access BaseSettings through pydantic.env_settings module
    env_settings_error = None
    try:
        _ = pydantic.env_settings.BaseSettings
    except PydanticImportError as e:
        env_settings_error = str(e)
    except AttributeError as e:
        env_settings_error = f"AttributeError: {e}"
    
    # The error messages should be consistent (both should be PydanticImportError)
    # But they're not - this is the bug
    assert pydantic_error is not None, "pydantic.BaseSettings should raise an error"
    assert "pydantic-settings" in pydantic_error, "Should mention pydantic-settings package"
    
    # This assertion will fail, demonstrating the bug
    assert env_settings_error is not None
    assert "AttributeError" not in env_settings_error, (
        f"env_settings.BaseSettings raises AttributeError instead of PydanticImportError. "
        f"Got: {env_settings_error}"
    )
    assert "pydantic-settings" in env_settings_error, (
        "Should mention pydantic-settings package consistently"
    )


@given(st.text(min_size=1, max_size=50))
def test_getattr_migration_module_parameter_handling(module_name):
    """
    Test that getattr_migration correctly uses the module parameter for import paths.
    
    The function builds import_path as f'{module}:{name}' but the BaseSettings
    check is hardcoded to only check 'pydantic:BaseSettings'.
    """
    assume(not module_name.startswith('_'))
    assume('.' in module_name)  # Only test dotted module names
    
    # Create a wrapper using getattr_migration
    wrapper = getattr_migration(module_name)
    
    # Try to access BaseSettings through this wrapper
    try:
        result = wrapper('BaseSettings')
        # If it doesn't raise an error, check if it's because the module name doesn't match
        import_path = f'{module_name}:BaseSettings'
        # The special case only triggers for 'pydantic:BaseSettings'
        if module_name != 'pydantic':
            # It should still provide meaningful error, not just AttributeError
            pass
    except PydanticImportError as e:
        # Should only happen if module_name == 'pydantic'
        assert module_name == 'pydantic', (
            f"PydanticImportError raised for module '{module_name}' "
            f"but should only trigger for 'pydantic'"
        )
        assert 'pydantic-settings' in str(e)
    except AttributeError as e:
        # This happens for other module names, but BaseSettings migration
        # should be consistent across all modules using getattr_migration
        error_msg = str(e)
        # Should not just be a generic AttributeError for BaseSettings
        if 'BaseSettings' in error_msg and module_name.startswith('pydantic'):
            # This is the inconsistency - BaseSettings should have special handling
            # regardless of the specific pydantic submodule
            pass