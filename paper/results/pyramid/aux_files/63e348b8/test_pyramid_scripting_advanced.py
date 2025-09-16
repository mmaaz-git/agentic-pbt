import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.scripting as scripting
from pyramid.scripting import AppEnvironment, prepare, get_root
from pyramid.config import Configurator
from pyramid.testing import DummyRequest
from unittest.mock import Mock, MagicMock, patch
import traceback


@given(st.integers(min_value=0, max_value=10))
def test_app_environment_nested_context_managers(depth):
    """Test AppEnvironment with nested context manager usage"""
    call_order = []
    
    def make_closer(id):
        def closer():
            call_order.append(id)
        return closer
    
    envs = []
    for i in range(depth):
        env = AppEnvironment({'closer': make_closer(i), 'id': i})
        envs.append(env)
    
    # Nest the context managers
    def nest(envs_list, idx=0):
        if idx >= len(envs_list):
            return
        with envs_list[idx]:
            nest(envs_list, idx + 1)
    
    nest(envs)
    
    # Closers should be called in reverse order (LIFO)
    expected_order = list(range(depth - 1, -1, -1))
    assert call_order == expected_order


@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=1))
def test_app_environment_iteration_consistency(data):
    """Test that AppEnvironment iteration is consistent with dict behavior"""
    data['closer'] = lambda: None
    env = AppEnvironment(data)
    
    # Test various iteration methods
    assert list(env.keys()) == list(data.keys())
    assert list(env.values()) == list(data.values())
    assert list(env.items()) == list(data.items())
    
    # Test that iteration order is preserved
    for env_key, data_key in zip(env, data):
        assert env_key == data_key


def test_prepare_registry_none_error():
    """Test that prepare raises ConfigurationError when no registry available"""
    # Clear global registries
    original_last = scripting.global_registries.last
    try:
        scripting.global_registries.last = None
        
        try:
            env = prepare()
            assert False, "Should have raised ConfigurationError"
        except scripting.ConfigurationError as e:
            assert "No valid Pyramid applications" in str(e)
    finally:
        scripting.global_registries.last = original_last


def test_prepare_finished_callbacks_called():
    """Test that request finished callbacks are invoked by closer (line 103-104)"""
    config = Configurator()
    registry = config.registry
    
    callback_called = False
    
    def callback(request):
        nonlocal callback_called
        callback_called = True
    
    # Create request with finished callback
    request = DummyRequest()
    request.add_finished_callback(callback)
    
    env = prepare(request=request, registry=registry)
    
    # Callback should not be called yet
    assert not callback_called
    
    # Call closer
    env['closer']()
    
    # Callback should now be called
    assert callback_called


@given(st.lists(st.text(min_size=1), min_size=1, max_size=5))
def test_prepare_multiple_finished_callbacks(callback_ids):
    """Test multiple finished callbacks are all called"""
    config = Configurator()
    registry = config.registry
    
    called_ids = []
    
    def make_callback(id):
        def callback(request):
            called_ids.append(id)
        return callback
    
    request = DummyRequest()
    for id in callback_ids:
        request.add_finished_callback(make_callback(id))
    
    env = prepare(request=request, registry=registry)
    env['closer']()
    
    # All callbacks should be called
    assert len(called_ids) == len(callback_ids)
    assert set(called_ids) == set(callback_ids)


def test_get_root_closer_cleans_up_context():
    """Test that get_root's closer properly cleans up RequestContext"""
    config = Configurator()
    app = config.make_wsgi_app()
    
    # Get root and closer
    root, closer = get_root(app)
    
    # Root should be returned
    assert root is not None
    
    # Closer should be callable
    assert callable(closer)
    
    # Call closer to clean up
    closer()
    
    # After cleanup, we should be able to call get_root again
    root2, closer2 = get_root(app)
    assert root2 is not None
    closer2()


@given(st.text(min_size=1, max_size=10))
def test_prepare_request_context_attribute(path):
    """Test that prepare sets request.context when not already set (lines 111-112)"""
    config = Configurator()
    registry = config.registry
    
    # Test with request that has no context
    request = DummyRequest()
    request.registry = registry
    
    env = prepare(request=request, registry=registry)
    
    # request.context should be set to root
    assert hasattr(env['request'], 'context')
    assert env['request'].context is env['root']
    
    env['closer']()
    
    # Test with request that already has context
    request2 = DummyRequest()
    request2.registry = registry
    request2.context = "existing_context"
    
    env2 = prepare(request=request2, registry=registry)
    
    # Should preserve existing context
    assert env2['request'].context == "existing_context"
    
    env2['closer']()


def test_app_environment_closer_exception_handling():
    """Test AppEnvironment.__exit__ when closer raises exception"""
    exception_raised = False
    
    def failing_closer():
        nonlocal exception_raised
        exception_raised = True
        raise ValueError("Closer failed")
    
    env = AppEnvironment({'closer': failing_closer})
    
    # Context manager should propagate the exception
    try:
        with env:
            pass
    except ValueError as e:
        assert str(e) == "Closer failed"
        assert exception_raised
    else:
        assert False, "Exception should have been raised"


@given(st.one_of(
    st.just(None),
    st.builds(lambda: object()),  # Non-callable object
    st.integers(),
    st.text()
))
def test_app_environment_invalid_closer(invalid_closer):
    """Test AppEnvironment behavior with invalid closer values"""
    env = AppEnvironment({'closer': invalid_closer})
    
    if callable(invalid_closer):
        # Should work fine
        with env:
            pass
    else:
        # Should raise TypeError when trying to call non-callable
        try:
            with env:
                pass
        except TypeError:
            pass  # Expected
        else:
            assert False, f"Should have raised TypeError for non-callable closer: {type(invalid_closer)}"


def test_get_root_with_custom_request():
    """Test get_root with a custom request object"""
    config = Configurator()
    app = config.make_wsgi_app()
    
    # Create custom request
    custom_request = DummyRequest(path='/custom/path')
    custom_request.custom_attr = "test_value"
    
    root, closer = get_root(app, request=custom_request)
    
    # Should use our custom request
    assert root is not None
    
    closer()