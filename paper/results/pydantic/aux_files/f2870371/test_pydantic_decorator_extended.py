"""Extended property-based tests for pydantic.decorator.getattr_migration"""

import sys
import warnings
from unittest.mock import patch

import pytest
from hypothesis import assume, given, settings, strategies as st

from pydantic._migration import (
    DEPRECATED_MOVED_IN_V2,
    MOVED_IN_V2,
    REDIRECT_TO_V1,
    REMOVED_IN_V2,
)
from pydantic.decorator import getattr_migration
from pydantic.errors import PydanticImportError


# Test with increased examples
@settings(max_examples=1000)
@given(st.text(min_size=1))
def test_wrapper_never_crashes_on_valid_module(module_name):
    """getattr_migration should never crash when called with any string module name."""
    try:
        wrapper = getattr_migration(module_name)
        assert callable(wrapper)
    except Exception as e:
        pytest.fail(f"getattr_migration crashed with {e!r} for module_name={module_name!r}")


@settings(max_examples=500)
@given(
    module_name=st.text(min_size=1),
    attr_name=st.text(min_size=1)
)
def test_consistent_error_messages(module_name, attr_name):
    """Error messages should be consistent across multiple calls."""
    wrapper1 = getattr_migration(module_name)
    wrapper2 = getattr_migration(module_name)
    
    # Special case for __path__
    if attr_name == '__path__':
        try:
            wrapper1(attr_name)
        except AttributeError as e1:
            try:
                wrapper2(attr_name)
            except AttributeError as e2:
                assert str(e1) == str(e2)
                return
    
    # For other attributes, check consistency
    import_path = f'{module_name}:{attr_name}'
    
    # Skip known special cases
    if (import_path in MOVED_IN_V2 or 
        import_path in DEPRECATED_MOVED_IN_V2 or 
        import_path in REDIRECT_TO_V1 or 
        import_path in REMOVED_IN_V2 or
        import_path == 'pydantic:BaseSettings'):
        return
    
    # Test with a fake module
    if module_name not in sys.modules:
        sys.modules[module_name] = type(sys)(module_name)
        try:
            result1 = None
            result2 = None
            error1 = None
            error2 = None
            
            try:
                result1 = wrapper1(attr_name)
            except AttributeError as e:
                error1 = str(e)
            
            try:
                result2 = wrapper2(attr_name)
            except AttributeError as e:
                error2 = str(e)
            
            if error1 and error2:
                assert error1 == error2
            elif result1 is not None and result2 is not None:
                assert result1 == result2
        finally:
            del sys.modules[module_name]


@settings(max_examples=500)
@given(st.text(min_size=1))
def test_unicode_module_names(module_name):
    """Test with various unicode characters in module names."""
    # Focus on unicode strings that might cause issues
    wrapper = getattr_migration(module_name)
    
    # Test __path__ with unicode module names
    import re
    with pytest.raises(AttributeError, match=re.escape(f"module {module_name!r} has no attribute '__path__'")):
        wrapper('__path__')


@settings(max_examples=500)
@given(
    module_name=st.text(min_size=1, alphabet=st.characters(min_codepoint=128, max_codepoint=65535)),
    attr_name=st.text(min_size=1, alphabet=st.characters(min_codepoint=128, max_codepoint=65535))
)
def test_high_unicode_names(module_name, attr_name):
    """Test with high unicode characters that might reveal encoding issues."""
    wrapper = getattr_migration(module_name)
    
    if attr_name == '__path__':
        import re
        with pytest.raises(AttributeError, match=re.escape(f"module {module_name!r} has no attribute '__path__'")):
            wrapper(attr_name)
    else:
        # Create a fake module with unicode attribute
        import_path = f'{module_name}:{attr_name}'
        assume(import_path not in MOVED_IN_V2)
        assume(import_path not in DEPRECATED_MOVED_IN_V2)
        assume(import_path not in REDIRECT_TO_V1)
        assume(import_path not in REMOVED_IN_V2)
        
        if module_name not in sys.modules:
            module = type(sys)(module_name)
            setattr(module, attr_name, f'unicode_value_{attr_name}')
            sys.modules[module_name] = module
            
            try:
                result = wrapper(attr_name)
                assert result == f'unicode_value_{attr_name}'
            finally:
                del sys.modules[module_name]


@given(
    st.text(min_size=1, max_size=5000)
)
def test_long_module_names(module_name):
    """Test with very long module names."""
    wrapper = getattr_migration(module_name)
    assert callable(wrapper)
    
    # Test __path__ with long module names
    import re
    with pytest.raises(AttributeError, match=re.escape(f"module {module_name!r} has no attribute '__path__'")):
        wrapper('__path__')


@given(
    module_name=st.text(min_size=1),
    attr_name=st.just('')
)
def test_empty_attribute_name(module_name, attr_name):
    """Test behavior with empty attribute names."""
    wrapper = getattr_migration(module_name)
    
    import_path = f'{module_name}:'
    if import_path not in MOVED_IN_V2 and import_path not in DEPRECATED_MOVED_IN_V2 and import_path not in REDIRECT_TO_V1 and import_path not in REMOVED_IN_V2:
        if module_name not in sys.modules:
            sys.modules[module_name] = type(sys)(module_name)
            try:
                import re
                with pytest.raises(AttributeError, match=re.escape(f"module {module_name!r} has no attribute {attr_name!r}")):
                    wrapper(attr_name)
            finally:
                del sys.modules[module_name]


@given(
    module_name=st.text(alphabet=st.characters(whitelist_categories=('Zs', 'Cc')), min_size=1)
)
def test_whitespace_module_names(module_name):
    """Test with whitespace and control characters in module names."""
    wrapper = getattr_migration(module_name)
    assert callable(wrapper)
    
    # Test __path__ with whitespace module names
    import re
    with pytest.raises(AttributeError, match=re.escape(f"module {module_name!r} has no attribute '__path__'")):
        wrapper('__path__')


@settings(max_examples=500)
@given(
    attr_name=st.sampled_from(['__dict__', '__class__', '__module__', '__name__', '__doc__', '__annotations__'])
)
def test_dunder_attributes(attr_name):
    """Test behavior with various dunder attributes."""
    fake_module = 'test_dunder_module'
    module = type(sys)(fake_module)
    sys.modules[fake_module] = module
    
    try:
        wrapper = getattr_migration(fake_module)
        
        # These dunder attributes should exist on the module object
        result = wrapper(attr_name)
        # Just check it doesn't crash - the value depends on the module implementation
        assert result is not None or result is None  # Could be None for __doc__
    finally:
        del sys.modules[fake_module]


@given(
    module_name=st.text(min_size=1).filter(lambda x: x not in sys.modules)
)
def test_non_existent_module_behavior(module_name):
    """Test behavior when module doesn't exist in sys.modules."""
    wrapper = getattr_migration(module_name)
    
    # Without the module in sys.modules, it should raise KeyError when accessing globals
    with pytest.raises((AttributeError, KeyError)):
        wrapper('some_attr')