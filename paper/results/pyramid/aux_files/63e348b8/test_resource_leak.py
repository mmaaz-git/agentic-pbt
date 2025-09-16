import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.scripting import get_root, prepare
from pyramid.threadlocal import get_current_request
from pyramid.config import Configurator
from unittest.mock import Mock
import traceback


def test_get_root_resource_leak_on_exception():
    """Test that get_root leaks RequestContext when root_factory raises exception"""
    
    # Create a mock app
    mock_app = Mock()
    mock_registry = Mock()
    mock_app.registry = mock_registry
    
    # Create a root factory that raises an exception
    def failing_root_factory(request):
        raise ValueError("Root factory failed")
    
    mock_app.root_factory = failing_root_factory
    
    # Mock the request factory
    mock_request = Mock()
    mock_request.registry = None
    mock_request_factory = Mock()
    mock_request_factory.blank = Mock(return_value=mock_request)
    mock_registry.queryUtility = Mock(return_value=mock_request_factory)
    
    # Before calling get_root, check if there's a current request
    try:
        before_request = get_current_request()
        print(f"Request before get_root: {before_request}")
    except:
        before_request = None
        print("No request before get_root")
    
    # Call get_root, which should fail
    try:
        root, closer = get_root(mock_app)
        print("ERROR: get_root should have raised exception")
    except ValueError as e:
        print(f"Expected exception: {e}")
    
    # After the exception, check if there's still a current request
    try:
        after_request = get_current_request()
        print(f"Request after failed get_root: {after_request}")
        if after_request is mock_request:
            print("BUG CONFIRMED: RequestContext was not cleaned up!")
            print("The request is still in the threadlocal stack")
            return True
    except:
        print("No request after failed get_root (correct behavior)")
        return False


def test_prepare_resource_leak_on_exception():
    """Test that prepare leaks RequestContext when root_factory raises exception"""
    
    config = Configurator()
    registry = config.registry
    
    # Mock the root factory to raise an exception
    def failing_root_factory(request):
        raise ValueError("Root factory failed")
    
    # Replace the default root factory
    from pyramid.interfaces import IRootFactory
    registry.registerUtility(failing_root_factory, IRootFactory)
    
    # Check before
    try:
        before_request = get_current_request()
        print(f"Request before prepare: {before_request}")
    except:
        before_request = None
        print("No request before prepare")
    
    # Call prepare, which should fail
    try:
        env = prepare(registry=registry)
        print("ERROR: prepare should have raised exception")
    except ValueError as e:
        print(f"Expected exception: {e}")
    
    # Check after - is the request still in threadlocal?
    try:
        after_request = get_current_request()
        print(f"Request after failed prepare: {after_request}")
        if after_request is not None and after_request is not before_request:
            print("BUG CONFIRMED: RequestContext was not cleaned up after exception!")
            print("The request is still in the threadlocal stack")
            return True
    except:
        print("No request after failed prepare (correct behavior)")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing get_root resource leak...")
    print("=" * 60)
    leak1 = test_get_root_resource_leak_on_exception()
    
    print("\n" + "=" * 60)
    print("Testing prepare resource leak...")
    print("=" * 60)
    leak2 = test_prepare_resource_leak_on_exception()
    
    print("\n" + "=" * 60)
    if leak1 or leak2:
        print("RESOURCE LEAK BUG FOUND!")
        print("When get_root() or prepare() fails due to root_factory exception,")
        print("the RequestContext is not properly cleaned up.")
    else:
        print("No resource leak detected")