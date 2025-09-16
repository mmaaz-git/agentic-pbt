import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
from pyramid.scripting import get_root, prepare
from pyramid.threadlocal import get_current_request
from pyramid.config import Configurator
from pyramid.interfaces import IRootFactory
from unittest.mock import Mock
import gc


@given(st.text(min_size=1, max_size=50))
def test_get_root_cleans_up_on_root_factory_exception(error_msg):
    """Property: get_root should always clean up RequestContext, even on exception"""
    
    # Create mock app with failing root factory
    mock_app = Mock()
    mock_registry = Mock()
    mock_app.registry = mock_registry
    
    def failing_root_factory(request):
        raise ValueError(error_msg)
    
    mock_app.root_factory = failing_root_factory
    
    # Mock request factory
    mock_request = Mock()
    mock_request.registry = None
    mock_request_factory = Mock()
    mock_request_factory.blank = Mock(return_value=mock_request)
    mock_registry.queryUtility = Mock(return_value=mock_request_factory)
    
    # Get initial state
    try:
        initial_request = get_current_request()
    except:
        initial_request = None
    
    # Call get_root (should fail)
    try:
        root, closer = get_root(mock_app)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected
    
    # Check final state
    try:
        final_request = get_current_request()
    except:
        final_request = None
    
    # Property: request state should be restored after exception
    # BUG: This assertion FAILS - the request is leaked!
    if initial_request is None:
        assert final_request is None, "RequestContext leaked - request still in threadlocal!"
    else:
        assert final_request is initial_request, "RequestContext state not restored!"


@given(st.text(min_size=1, max_size=50))
def test_prepare_cleans_up_on_root_factory_exception(error_msg):
    """Property: prepare should always clean up RequestContext, even on exception"""
    
    config = Configurator()
    registry = config.registry
    
    # Register failing root factory
    def failing_root_factory(request):
        raise ValueError(error_msg)
    
    registry.registerUtility(failing_root_factory, IRootFactory)
    
    # Get initial state
    try:
        initial_request = get_current_request()
    except:
        initial_request = None
    
    # Call prepare (should fail)
    try:
        env = prepare(registry=registry)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected
    
    # Check final state
    try:
        final_request = get_current_request()
    except:
        final_request = None
    
    # Property: request state should be restored after exception
    # BUG: This assertion FAILS - the request is leaked!
    if initial_request is None:
        assert final_request is None, "RequestContext leaked - request still in threadlocal!"
    else:
        assert final_request is initial_request, "RequestContext state not restored!"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])