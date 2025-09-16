"""Property-based tests for pydantic.class_validators.getattr_migration"""

import sys
from hypothesis import given, strategies as st, assume
import pydantic.class_validators
import pydantic._migration


# Strategy for module names - mix of real and fake modules
module_names = st.one_of(
    st.sampled_from([
        'pydantic',
        'pydantic.utils',
        'pydantic.errors',
        'pydantic.typing',
        'pydantic.fields',
        'nonexistent_module',
        'fake.module.path',
    ]),
    st.text(min_size=1, max_size=50).filter(lambda x: '.' not in x or all(part for part in x.split('.'))),
)

# Strategy for attribute names
attr_names = st.one_of(
    st.sampled_from([
        'version_info',
        'ValidationError',
        'to_camel',
        '__path__',
        '__name__',
        'BaseSettings',
        'does_not_exist',
    ]),
    st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier() or x.startswith('__') and x.endswith('__')),
)


@given(module_names, attr_names)
def test_getattr_migration_no_keyerror(module_name, attr_name):
    """The function should never raise KeyError, only AttributeError or PydanticImportError"""
    migration_func = pydantic.class_validators.getattr_migration(module_name)
    
    try:
        result = migration_func(attr_name)
    except AttributeError:
        pass  # This is expected for invalid attributes
    except ImportError:
        pass  # This can happen for import errors
    except KeyError as e:
        # This should never happen - it's a bug
        raise AssertionError(f"Unexpected KeyError: {e}")


@given(module_names, attr_names)
def test_getattr_migration_consistency(module_name, attr_name):
    """Multiple calls with same inputs should behave consistently"""
    migration_func1 = pydantic.class_validators.getattr_migration(module_name)
    migration_func2 = pydantic.class_validators.getattr_migration(module_name)
    
    # Both functions should behave the same way
    result1 = None
    error1 = None
    result2 = None
    error2 = None
    
    try:
        result1 = migration_func1(attr_name)
    except Exception as e:
        error1 = type(e)
    
    try:
        result2 = migration_func2(attr_name)
    except Exception as e:
        error2 = type(e)
    
    # Either both succeed or both fail with same error type
    if error1 is None:
        assert error2 is None, f"Inconsistent behavior: first succeeded, second raised {error2}"
        assert result1 == result2, f"Different results: {result1} != {result2}"
    else:
        assert error1 == error2, f"Different error types: {error1} != {error2}"


@given(st.text(min_size=1, max_size=50))
def test_module_not_in_sys_modules(module_name):
    """Test behavior when module is not in sys.modules"""
    # Ensure module is not in sys.modules
    assume(module_name not in sys.modules)
    assume('.' in module_name or module_name.isidentifier())
    
    migration_func = pydantic.class_validators.getattr_migration(module_name)
    
    # Try to access an attribute that won't be in migration dicts
    try:
        result = migration_func('nonexistent_attribute_xyz123')
    except AttributeError:
        pass  # Expected
    except KeyError as e:
        # This is the bug - should be AttributeError not KeyError
        raise AssertionError(f"Got KeyError instead of AttributeError: {e}")


@given(module_names)
def test_dunder_path_always_raises_attribute_error(module_name):
    """__path__ should always raise AttributeError per the implementation"""
    migration_func = pydantic.class_validators.getattr_migration(module_name)
    
    try:
        result = migration_func('__path__')
        raise AssertionError(f"Expected AttributeError for __path__, got {result}")
    except AttributeError as e:
        assert '__path__' in str(e)
    except Exception as e:
        raise AssertionError(f"Expected AttributeError, got {type(e).__name__}: {e}")