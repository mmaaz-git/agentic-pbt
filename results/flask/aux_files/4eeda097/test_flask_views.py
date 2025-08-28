import string
from typing import Any
from unittest.mock import Mock, patch

import flask
from flask.views import MethodView, View, http_method_funcs
from hypothesis import assume, given, strategies as st


@st.composite
def valid_python_identifier(draw):
    first_char = draw(st.sampled_from(string.ascii_letters + "_"))
    rest = draw(st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=0, max_size=20))
    return first_char + rest


@st.composite
def http_method_subset(draw):
    methods = list(http_method_funcs)
    subset = draw(st.lists(st.sampled_from(methods), min_size=1, max_size=len(methods), unique=True))
    return subset


@given(methods=http_method_subset())
def test_methodview_methods_automatic_detection(methods):
    """Test that MethodView automatically detects HTTP methods defined on the class."""
    
    class TestView(MethodView):
        pass
    
    # Dynamically add methods to the class
    for method in methods:
        setattr(TestView, method, lambda self: "response")
    
    # Methods should be automatically set to uppercase versions of defined methods
    expected_methods = {m.upper() for m in methods}
    assert TestView.methods == expected_methods, f"Expected {expected_methods}, got {TestView.methods}"


@given(
    view_name=valid_python_identifier(),
    num_decorators=st.integers(min_value=1, max_value=5)
)
def test_view_decorator_order_preservation(view_name, num_decorators):
    """Test that decorators are applied in the correct order."""
    
    call_order = []
    decorators = []
    
    for i in range(num_decorators):
        def make_decorator(idx):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    call_order.append(idx)
                    return func(*args, **kwargs)
                wrapper.__name__ = func.__name__
                return wrapper
            return decorator
        decorators.append(make_decorator(i))
    
    class TestView(View):
        decorators = decorators
        
        def dispatch_request(self):
            return "response"
    
    with patch('flask.views.current_app') as mock_app:
        mock_app.ensure_sync = lambda f: f
        view_func = TestView.as_view(view_name)
        
        # Call the view function to trigger decorators
        view_func()
        
        # Check that decorators were called in the correct order
        assert call_order == list(range(num_decorators)), f"Decorators called in wrong order: {call_order}"


@given(has_get=st.booleans(), has_head=st.booleans())
def test_methodview_head_fallback(has_get, has_head):
    """Test that HEAD requests fall back to GET when no HEAD handler exists."""
    
    class TestView(MethodView):
        pass
    
    if has_get:
        TestView.get = lambda self: "GET response"
    if has_head:
        TestView.head = lambda self: "HEAD response"
    
    view = TestView()
    
    with patch('flask.views.request') as mock_request:
        with patch('flask.views.current_app') as mock_app:
            mock_app.ensure_sync = lambda f: f
            
            # Test HEAD request
            mock_request.method = "HEAD"
            
            if has_head:
                # Should use HEAD handler
                result = view.dispatch_request()
                assert result == "HEAD response"
            elif has_get:
                # Should fall back to GET
                result = view.dispatch_request()
                assert result == "GET response"
            else:
                # Should raise assertion error
                try:
                    view.dispatch_request()
                    assert False, "Should have raised AssertionError"
                except AssertionError as e:
                    assert "Unimplemented method 'HEAD'" in str(e)


@given(
    view_name=valid_python_identifier(),
    init_every_request=st.booleans(),
    num_calls=st.integers(min_value=2, max_value=10)
)
def test_view_init_every_request_behavior(view_name, init_every_request, num_calls):
    """Test that init_every_request controls instance reuse correctly."""
    
    instances = []
    
    class TestView(View):
        init_every_request = init_every_request
        
        def __init__(self):
            instances.append(self)
        
        def dispatch_request(self):
            return "response"
    
    with patch('flask.views.current_app') as mock_app:
        mock_app.ensure_sync = lambda f: f
        view_func = TestView.as_view(view_name)
        
        # Call the view function multiple times
        for _ in range(num_calls):
            view_func()
        
        if init_every_request:
            # Should create a new instance for each request
            assert len(instances) == num_calls, f"Expected {num_calls} instances, got {len(instances)}"
            # All instances should be different
            assert len(set(id(inst) for inst in instances)) == num_calls
        else:
            # Should reuse the same instance
            assert len(instances) == 1, f"Expected 1 instance, got {len(instances)}"


@given(
    view_name=valid_python_identifier(),
    class_doc=st.text(min_size=0, max_size=100),
    methods_list=st.lists(st.sampled_from(['GET', 'POST', 'PUT', 'DELETE']), min_size=0, max_size=4, unique=True)
)
def test_view_function_attribute_preservation(view_name, class_doc, methods_list):
    """Test that generated view function preserves class attributes."""
    
    class TestView(View):
        methods = set(methods_list) if methods_list else None
        provide_automatic_options = False
        
        def dispatch_request(self):
            return "response"
    
    TestView.__doc__ = class_doc
    
    with patch('flask.views.current_app') as mock_app:
        mock_app.ensure_sync = lambda f: f
        view_func = TestView.as_view(view_name)
        
        # Check attribute preservation
        assert view_func.__name__ == view_name
        assert view_func.__doc__ == class_doc
        assert view_func.__module__ == TestView.__module__
        assert view_func.view_class == TestView
        assert view_func.methods == TestView.methods
        assert view_func.provide_automatic_options == TestView.provide_automatic_options


@given(method_name=st.sampled_from(list(http_method_funcs)))
def test_methodview_case_insensitive_dispatch(method_name):
    """Test that MethodView correctly dispatches methods regardless of case."""
    
    class TestView(MethodView):
        pass
    
    # Add the method handler
    setattr(TestView, method_name, lambda self: f"{method_name} response")
    
    view = TestView()
    
    with patch('flask.views.request') as mock_request:
        with patch('flask.views.current_app') as mock_app:
            mock_app.ensure_sync = lambda f: f
            
            # Test with uppercase method (as it would come from HTTP)
            mock_request.method = method_name.upper()
            
            result = view.dispatch_request()
            assert result == f"{method_name} response"


@given(
    base_methods=st.lists(st.sampled_from(list(http_method_funcs)), min_size=0, max_size=3, unique=True),
    child_methods=st.lists(st.sampled_from(list(http_method_funcs)), min_size=0, max_size=3, unique=True)
)
def test_methodview_method_inheritance(base_methods, child_methods):
    """Test that MethodView correctly inherits methods from base classes."""
    
    class BaseView(MethodView):
        pass
    
    for method in base_methods:
        setattr(BaseView, method, lambda self: f"base_{method}")
    
    class ChildView(BaseView):
        pass
    
    for method in child_methods:
        setattr(ChildView, method, lambda self: f"child_{method}")
    
    # Child should have union of both method sets
    all_methods = set(base_methods) | set(child_methods)
    expected_methods = {m.upper() for m in all_methods}
    
    assert ChildView.methods == expected_methods or (not all_methods and ChildView.methods is None)


@given(
    num_args=st.integers(min_value=0, max_value=5),
    num_kwargs=st.integers(min_value=0, max_value=5)
)
def test_view_as_view_argument_forwarding(num_args, num_kwargs):
    """Test that as_view correctly forwards arguments to __init__."""
    
    init_args = []
    init_kwargs = {}
    
    class TestView(View):
        def __init__(self, *args, **kwargs):
            init_args.extend(args)
            init_kwargs.update(kwargs)
        
        def dispatch_request(self):
            return "response"
    
    # Generate test arguments
    test_args = [f"arg{i}" for i in range(num_args)]
    test_kwargs = {f"kwarg{i}": f"value{i}" for i in range(num_kwargs)}
    
    with patch('flask.views.current_app') as mock_app:
        mock_app.ensure_sync = lambda f: f
        view_func = TestView.as_view("test", *test_args, **test_kwargs)
        
        # Call the view to trigger initialization
        view_func()
        
        # Check that arguments were forwarded correctly
        assert init_args == test_args
        assert init_kwargs == test_kwargs