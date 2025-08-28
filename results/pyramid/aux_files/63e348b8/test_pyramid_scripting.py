import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.scripting as scripting
from pyramid.scripting import AppEnvironment, prepare, get_root, _make_request
from pyramid.config import Configurator
from pyramid.testing import DummyRequest
from unittest.mock import Mock, MagicMock
import traceback


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_app_environment_is_dict_subclass(data):
    """AppEnvironment should behave like a dict (line 122: class AppEnvironment(dict))"""
    env = AppEnvironment(data)
    
    # Should support all dict operations
    assert isinstance(env, dict)
    assert dict(env) == data
    assert len(env) == len(data)
    
    # Should support dict methods
    for key, value in data.items():
        assert key in env
        assert env[key] == value
        assert env.get(key) == value
    
    # Should support dict updates
    new_key = 'test_key_xyz'
    assume(new_key not in data)
    env[new_key] = 'test_value'
    assert env[new_key] == 'test_value'
    assert new_key in env


@given(st.text(min_size=1))
def test_app_environment_context_manager_calls_closer(mock_closer_key):
    """AppEnvironment.__exit__ should call self['closer']() (lines 126-127)"""
    closer_called = False
    
    def mock_closer():
        nonlocal closer_called
        closer_called = True
    
    # Create AppEnvironment with a closer
    env = AppEnvironment({'closer': mock_closer, mock_closer_key: 'value'})
    
    # Use as context manager
    with env as e:
        assert e is env
        assert not closer_called
    
    # After exiting, closer should have been called
    assert closer_called


@given(st.text(min_size=1, max_size=100))
def test_make_request_preserves_path(path):
    """_make_request should create a request with the given path (line 152)"""
    # Create a minimal registry with request factory
    config = Configurator()
    registry = config.registry
    
    # Make request with the path
    request = _make_request(path, registry=registry)
    
    # The request should have the path we provided
    assert request.path == path
    assert request.registry is registry


def test_prepare_returns_required_keys():
    """prepare() should return dict with specific keys (lines 113-119)"""
    # Create a minimal Pyramid app configuration
    config = Configurator()
    registry = config.registry
    
    # Call prepare
    env = prepare(registry=registry)
    
    # Check all required keys are present
    required_keys = ['root', 'closer', 'registry', 'request', 'root_factory']
    for key in required_keys:
        assert key in env, f"Missing required key: {key}"
    
    # Verify it's an AppEnvironment
    assert isinstance(env, AppEnvironment)
    assert isinstance(env, dict)
    
    # Verify closer is callable
    assert callable(env['closer'])
    
    # Clean up
    env['closer']()


def test_get_root_returns_tuple():
    """get_root() should return (root, closer) tuple (line 32)"""
    # Create a mock app with necessary attributes
    mock_app = Mock()
    mock_registry = Mock()
    mock_app.registry = mock_registry
    
    # Mock root factory
    mock_root = Mock()
    mock_app.root_factory = Mock(return_value=mock_root)
    
    # Mock request factory in registry
    mock_request_factory = Mock()
    mock_request_factory.blank = Mock(return_value=Mock(registry=None))
    mock_registry.queryUtility = Mock(return_value=mock_request_factory)
    
    # Call get_root
    result = get_root(mock_app)
    
    # Should return a tuple with exactly 2 elements
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    root, closer = result
    assert root is mock_root
    assert callable(closer)
    
    # Clean up
    closer()


@given(st.dictionaries(
    st.sampled_from(['root', 'closer', 'registry', 'request', 'root_factory']),
    st.integers(),
    min_size=5,
    max_size=5
))
def test_app_environment_preserves_dict_semantics_with_closer(data):
    """AppEnvironment with 'closer' key should still behave as a normal dict"""
    # Make closer callable
    data['closer'] = lambda: None
    
    env = AppEnvironment(data)
    
    # All dict operations should work normally
    assert len(env) == 5
    assert set(env.keys()) == set(data.keys())
    
    # Context manager should work without error
    with env:
        pass  # closer gets called on exit
    
    # Dict should still be usable after context manager exit
    assert len(env) == 5
    assert 'closer' in env


@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_app_environment_multiple_context_manager_uses(keys):
    """AppEnvironment should handle multiple context manager uses"""
    call_count = 0
    
    def counting_closer():
        nonlocal call_count
        call_count += 1
    
    # Create env with unique keys
    data = {key: f'value_{i}' for i, key in enumerate(set(keys))}
    data['closer'] = counting_closer
    env = AppEnvironment(data)
    
    # Use as context manager multiple times
    for i in range(3):
        with env:
            assert call_count == i
        assert call_count == i + 1
    
    assert call_count == 3


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=100))
def test_make_request_with_special_characters(path):
    """_make_request should handle paths with special characters"""
    config = Configurator()
    registry = config.registry
    
    try:
        request = _make_request(path, registry=registry)
        assert request.path == path
    except Exception as e:
        # If it fails, it should be a clear error, not a crash
        assert isinstance(e, (ValueError, TypeError, AttributeError))


@given(st.one_of(
    st.none(),
    st.builds(lambda: Mock(registry=Mock()))
))
def test_prepare_handles_request_parameter(request):
    """prepare() should handle both None and actual request objects (lines 92-97)"""
    config = Configurator()
    registry = config.registry
    
    # Should not crash regardless of request parameter
    env = prepare(request=request, registry=registry)
    
    assert 'request' in env
    assert 'registry' in env
    assert env['registry'] is registry
    
    # Clean up
    env['closer']()