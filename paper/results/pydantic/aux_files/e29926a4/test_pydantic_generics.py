"""Property-based tests for pydantic.generics module."""

import sys
from hypothesis import given, strategies as st, assume, settings
import pydantic.generics
from pydantic._migration import getattr_migration


# Test 1: Idempotence - calling wrapper multiple times with same input gives same result
@given(
    module_name=st.text(min_size=1, max_size=100).filter(lambda x: '.' not in x and not x.startswith('_')),
    attr_name=st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith('_'))
)
def test_getattr_migration_idempotence(module_name, attr_name):
    """Test that getattr_migration wrapper is idempotent."""
    # Skip if module name conflicts with actual modules
    assume(module_name not in sys.modules)
    
    wrapper = getattr_migration(module_name)
    
    # Call wrapper multiple times - should get same result/exception
    results = []
    exceptions = []
    
    for _ in range(3):
        try:
            result = wrapper(attr_name)
            results.append(result)
        except Exception as e:
            exceptions.append((type(e), str(e)))
    
    # All results should be identical or all should raise same exception
    if results:
        assert all(r == results[0] for r in results), f"Non-idempotent results for {attr_name}"
    if exceptions:
        assert all(e == exceptions[0] for e in exceptions), f"Non-idempotent exceptions for {attr_name}"


# Test 2: __path__ special case should always raise AttributeError
@given(module_name=st.text(min_size=1, max_size=100).filter(lambda x: '.' not in x))
def test_path_attribute_always_raises(module_name):
    """Test that __path__ always raises AttributeError."""
    wrapper = getattr_migration(module_name)
    
    try:
        wrapper('__path__')
        assert False, "__path__ should always raise AttributeError"
    except AttributeError as e:
        assert '__path__' in str(e)
        assert module_name in str(e)
    except Exception as e:
        assert False, f"Expected AttributeError for __path__, got {type(e).__name__}: {e}"


# Test 3: Error message consistency
@given(
    module_name=st.text(min_size=1, max_size=100).filter(lambda x: '.' not in x and not x.startswith('_')),
    attr_name=st.text(min_size=1, max_size=100).filter(lambda x: x not in ['__path__'] and not x.startswith('_'))
)
def test_error_message_contains_names(module_name, attr_name):
    """Test that error messages contain module and attribute names."""
    assume(module_name not in sys.modules)
    
    wrapper = getattr_migration(module_name)
    
    # For non-existent attributes, error should mention both module and attribute
    try:
        wrapper(attr_name)
    except AttributeError as e:
        error_msg = str(e)
        # The error message should contain both the module name and attribute name
        assert module_name in error_msg or repr(module_name) in error_msg, \
            f"Module name {module_name} not in error: {error_msg}"
        assert attr_name in error_msg or repr(attr_name) in error_msg, \
            f"Attribute name {attr_name} not in error: {error_msg}"
    except Exception:
        # Other exceptions are fine - might be import errors, etc.
        pass


# Test 4: Module behavior - actual pydantic.generics module
@given(attr_name=st.text(min_size=1, max_size=100))
def test_pydantic_generics_module_behavior(attr_name):
    """Test the actual pydantic.generics module's __getattr__ behavior."""
    # Test that accessing non-existent attributes raises AttributeError
    if attr_name not in ['getattr_migration', '__getattr__', '__builtins__', '__cached__', 
                         '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__']:
        try:
            getattr(pydantic.generics, attr_name)
        except AttributeError as e:
            # Should raise AttributeError for non-existent attributes
            assert 'pydantic.generics' in str(e) or 'has no attribute' in str(e)
        except Exception:
            # Other exceptions might occur for special imports
            pass


# Test 5: Wrapper function type consistency
@given(module_name=st.text(min_size=1, max_size=50))
def test_wrapper_is_callable(module_name):
    """Test that getattr_migration always returns a callable."""
    wrapper = getattr_migration(module_name)
    assert callable(wrapper), f"getattr_migration should return a callable for module {module_name}"


# Test 6: Empty string edge cases
def test_edge_cases():
    """Test edge cases with empty strings and special characters."""
    # Empty module name
    wrapper = getattr_migration("")
    try:
        wrapper("test")
    except AttributeError:
        pass  # Expected
    
    # Module with special characters
    wrapper = getattr_migration("test-module!@#")
    try:
        wrapper("attr")
    except AttributeError:
        pass  # Expected


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])