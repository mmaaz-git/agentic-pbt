import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pyramid.scripting as scripting
from pyramid.scripting import AppEnvironment, prepare, get_root
from pyramid.config import Configurator
from pyramid.testing import DummyRequest
from unittest.mock import Mock, MagicMock, patch
import gc
import weakref


def test_app_environment_missing_closer_key():
    """Test AppEnvironment.__exit__ when 'closer' key is missing"""
    env = AppEnvironment({'data': 'value'})  # No 'closer' key
    
    try:
        with env:
            pass
    except KeyError as e:
        # This is what happens - it tries to call self['closer']
        assert 'closer' in str(e)
    else:
        assert False, "Should have raised KeyError"


def test_app_environment_del_closer_during_context():
    """Test deleting 'closer' key while in context manager"""
    closer_called = False
    
    def closer():
        nonlocal closer_called
        closer_called = True
    
    env = AppEnvironment({'closer': closer})
    
    try:
        with env:
            del env['closer']  # Delete closer while in context
    except KeyError:
        # Should raise KeyError when trying to call deleted closer
        assert not closer_called
    else:
        assert False, "Should have raised KeyError"


def test_app_environment_modify_closer_during_context():
    """Test modifying 'closer' while in context manager"""
    first_called = False
    second_called = False
    
    def first_closer():
        nonlocal first_called
        first_called = True
    
    def second_closer():
        nonlocal second_called
        second_called = True
    
    env = AppEnvironment({'closer': first_closer})
    
    with env:
        env['closer'] = second_closer  # Replace closer while in context
    
    # Should call the new closer, not the original
    assert not first_called
    assert second_called


@given(st.integers(min_value=1, max_value=100))
def test_app_environment_recursive_closer(depth):
    """Test AppEnvironment with a closer that modifies the env"""
    call_count = [0]
    
    def recursive_closer():
        call_count[0] += 1
        if call_count[0] < depth:
            # Closer modifies itself
            env['closer'] = recursive_closer
            with env:
                pass
    
    env = AppEnvironment({'closer': recursive_closer})
    
    with env:
        pass
    
    # Should have been called depth times
    assert call_count[0] == depth


def test_prepare_with_request_registry_mismatch():
    """Test prepare when request has different registry than provided"""
    config1 = Configurator()
    config2 = Configurator()
    registry1 = config1.registry
    registry2 = config2.registry
    
    # Create request with registry1
    request = DummyRequest()
    request.registry = registry1
    
    # Call prepare with registry2
    env = prepare(request=request, registry=registry2)
    
    # Should use registry2 (the explicitly provided one)
    assert env['registry'] is registry2
    assert env['request'].registry is registry2  # Request registry gets overwritten
    
    env['closer']()


def test_get_root_app_without_root_factory():
    """Test get_root when app doesn't have root_factory attribute"""
    mock_app = Mock()
    mock_app.registry = Mock()
    
    # Don't set root_factory attribute
    del mock_app.root_factory
    
    try:
        root, closer = get_root(mock_app)
        assert False, "Should have raised AttributeError"
    except AttributeError:
        pass  # Expected


def test_prepare_root_factory_returns_none():
    """Test prepare when root factory returns None"""
    config = Configurator()
    registry = config.registry
    
    # Mock root factory to return None
    with patch('pyramid.scripting.DefaultRootFactory', return_value=None):
        env = prepare(registry=registry)
        
        # Root should be None
        assert env['root'] is None
        
        # request.context should also be None
        assert env['request'].context is None
        
        env['closer']()


def test_app_environment_subclass_override():
    """Test that AppEnvironment subclass can override __exit__"""
    exit_called = False
    
    class CustomAppEnvironment(AppEnvironment):
        def __exit__(self, type, value, traceback):
            nonlocal exit_called
            exit_called = True
            # Don't call closer
            return False
    
    env = CustomAppEnvironment({'closer': lambda: 1/0})  # Closer would raise error
    
    with env:
        pass
    
    assert exit_called
    # No exception raised because we didn't call closer


@given(st.lists(st.text(min_size=1), min_size=0, max_size=1000))
def test_app_environment_large_dict_operations(keys):
    """Test AppEnvironment with large number of keys"""
    # Create large dict
    data = {f'key_{i}_{key}': i for i, key in enumerate(keys)}
    data['closer'] = lambda: None
    
    env = AppEnvironment(data)
    
    # Should handle large dicts efficiently
    assert len(env) == len(data)
    
    # All operations should work
    for key in data:
        assert key in env
    
    # Context manager should work
    with env:
        pass


def test_get_root_with_failing_root_factory():
    """Test get_root when root_factory raises exception"""
    mock_app = Mock()
    mock_app.registry = Mock()
    
    # Root factory that raises exception
    def failing_factory(request):
        raise ValueError("Root factory failed")
    
    mock_app.root_factory = failing_factory
    
    # Mock request factory
    mock_request_factory = Mock()
    mock_request_factory.blank = Mock(return_value=Mock(registry=None))
    mock_app.registry.queryUtility = Mock(return_value=mock_request_factory)
    
    try:
        root, closer = get_root(mock_app)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Root factory failed"
        # Note: RequestContext.begin() was called but not end()
        # This could be a resource leak!


def test_prepare_with_circular_reference():
    """Test prepare with circular references in request"""
    config = Configurator()
    registry = config.registry
    
    request = DummyRequest()
    request.circular = request  # Circular reference
    
    env = prepare(request=request, registry=registry)
    
    # Should handle circular references
    assert env['request'] is request
    assert env['request'].circular is request
    
    env['closer']()


@given(st.sampled_from([float('inf'), float('-inf'), float('nan')]))
def test_app_environment_with_special_float_values(value):
    """Test AppEnvironment with special float values"""
    env = AppEnvironment({'value': value, 'closer': lambda: None})
    
    # Should handle special floats
    assert 'value' in env
    
    with env:
        pass


def test_prepare_weak_reference_cleanup():
    """Test that prepare doesn't prevent garbage collection"""
    config = Configurator()
    registry = config.registry
    
    # Create env and get weak reference
    env = prepare(registry=registry)
    weak_env = weakref.ref(env)
    
    # Close and delete
    env['closer']()
    request_ref = weakref.ref(env['request'])
    del env
    
    # Force garbage collection
    gc.collect()
    
    # env should be collected (unless there's a leak)
    assert weak_env() is None
    # Note: request might still exist due to RequestContext