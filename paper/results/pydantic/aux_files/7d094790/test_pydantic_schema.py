import sys
from hypothesis import given, strategies as st, assume, settings
import pytest
from pydantic.schema import getattr_migration


@given(
    module_name=st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith('_')),
    attr_name=st.text(min_size=1, max_size=100)
)
def test_getattr_migration_deterministic(module_name, attr_name):
    """Test that getattr_migration returns consistent results for same inputs."""
    wrapper1 = getattr_migration(module_name)
    wrapper2 = getattr_migration(module_name)
    
    # Both wrappers should behave identically
    try:
        result1 = wrapper1(attr_name)
        result2 = wrapper2(attr_name)
        assert result1 == result2
    except Exception as e1:
        try:
            wrapper2(attr_name)
            assert False, f"First call raised {e1}, second didn't"
        except Exception as e2:
            assert type(e1) == type(e2)
            assert str(e1) == str(e2)


@given(module_name=st.text(min_size=1, max_size=100))
def test_getattr_migration_path_attribute(module_name):
    """Test that accessing __path__ always raises AttributeError with correct format."""
    wrapper = getattr_migration(module_name)
    
    with pytest.raises(AttributeError) as exc_info:
        wrapper('__path__')
    
    error_msg = str(exc_info.value)
    assert f"module {module_name!r}" in error_msg
    assert "__path__" in error_msg
    assert "has no attribute" in error_msg


@given(
    module_name=st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith('_')),
    attr_name=st.text(min_size=1, max_size=100).filter(lambda x: x != '__path__')
)
def test_getattr_migration_error_message_format(module_name, attr_name):
    """Test that error messages contain module and attribute names."""
    # Avoid names that might exist in globals
    assume(attr_name not in ['__name__', '__doc__', '__file__', '__spec__', 
                             '__loader__', '__package__', '__cached__'])
    assume(module_name not in sys.modules)  # Don't test existing modules
    
    wrapper = getattr_migration(module_name)
    
    # Create a fake module to test against - use types.ModuleType
    import types
    fake_module = types.ModuleType(module_name)
    sys.modules[module_name] = fake_module
    
    try:
        wrapper(attr_name)
    except AttributeError as e:
        error_msg = str(e)
        assert module_name in error_msg or repr(module_name) in error_msg
        assert attr_name in error_msg or repr(attr_name) in error_msg
    except Exception:
        pass  # Other exceptions are OK
    finally:
        # Clean up
        if module_name in sys.modules:
            del sys.modules[module_name]


@given(
    module_name=st.text(min_size=1, max_size=100),
    attr_name=st.text(min_size=1, max_size=100)
)
def test_getattr_migration_idempotent(module_name, attr_name):
    """Test that calling wrapper multiple times produces same result."""
    wrapper = getattr_migration(module_name)
    
    results = []
    exceptions = []
    
    for _ in range(3):
        try:
            result = wrapper(attr_name)
            results.append(result)
        except Exception as e:
            exceptions.append((type(e), str(e)))
    
    # Either all succeed with same result or all fail with same exception
    if results:
        assert all(r == results[0] for r in results), "Results differ across calls"
    if exceptions:
        assert all(e == exceptions[0] for e in exceptions), "Exceptions differ across calls"


@given(
    module_name=st.text(min_size=1, max_size=100).filter(lambda x: ':' not in x),
    attr_names=st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=5)
)
def test_getattr_migration_no_side_effects(module_name, attr_names):
    """Test that wrapper calls don't affect each other."""
    assume(all(':' not in name for name in attr_names))
    assume(len(set(attr_names)) == len(attr_names))  # All unique
    
    wrapper = getattr_migration(module_name)
    
    # Get baseline behavior for each attribute
    baseline = {}
    for name in attr_names:
        try:
            baseline[name] = ('success', wrapper(name))
        except Exception as e:
            baseline[name] = ('error', type(e).__name__, str(e))
    
    # Access them again in different order and verify same behavior
    for name in reversed(attr_names):
        try:
            result = wrapper(name)
            assert baseline[name][0] == 'success'
            assert baseline[name][1] == result
        except Exception as e:
            assert baseline[name][0] == 'error'
            assert baseline[name][1] == type(e).__name__
            assert baseline[name][2] == str(e)


@given(st.text(min_size=1, max_size=100))
def test_wrapper_callable(module_name):
    """Test that getattr_migration always returns a callable."""
    wrapper = getattr_migration(module_name)
    assert callable(wrapper)


@given(
    module_name=st.text(min_size=1).filter(lambda x: not any(c in x for c in [':', '\x00', '\n', '\r'])),
    attr_name=st.sampled_from(['BaseSettings'])
)
def test_special_basesettings_error(module_name, attr_name):
    """Test that BaseSettings from pydantic raises specific error."""
    if module_name == 'pydantic':
        wrapper = getattr_migration(module_name)
        from pydantic.errors import PydanticImportError
        
        with pytest.raises(PydanticImportError) as exc_info:
            wrapper('BaseSettings')
        
        error_msg = str(exc_info.value)
        assert 'pydantic-settings' in error_msg