import string
from typing import Any

import flask
from flask.views import MethodView, View, http_method_funcs
from hypothesis import assume, given, strategies as st


@st.composite
def valid_python_identifier(draw):
    first_char = draw(st.sampled_from(string.ascii_letters + "_"))
    rest = draw(st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=0, max_size=20))
    return first_char + rest


@given(
    view_name=valid_python_identifier(),
    num_decorators=st.integers(min_value=1, max_value=5)
)
def test_view_decorator_order_preservation(view_name, num_decorators):
    """Test that decorators are applied in the correct order."""
    
    app = flask.Flask(__name__)
    call_order = []
    test_decorators = []
    
    for i in range(num_decorators):
        def make_decorator(idx):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    call_order.append(idx)
                    return func(*args, **kwargs)
                wrapper.__name__ = func.__name__
                return wrapper
            return decorator
        test_decorators.append(make_decorator(i))
    
    class TestView(View):
        decorators = test_decorators
        
        def dispatch_request(self):
            return "response"
    
    with app.app_context():
        view_func = TestView.as_view(view_name)
        view_func()
        
        # Check that decorators were called in the correct order
        assert call_order == list(range(num_decorators)), f"Decorators called in wrong order: {call_order}"


@given(has_get=st.booleans(), has_head=st.booleans())
def test_methodview_head_fallback(has_get, has_head):
    """Test that HEAD requests fall back to GET when no HEAD handler exists."""
    
    app = flask.Flask(__name__)
    
    # Define class with methods in the class body
    if has_get and has_head:
        class TestView(MethodView):
            def get(self):
                return "GET response"
            def head(self):
                return "HEAD response"
    elif has_get:
        class TestView(MethodView):
            def get(self):
                return "GET response"
    elif has_head:
        class TestView(MethodView):
            def head(self):
                return "HEAD response"
    else:
        class TestView(MethodView):
            pass
    
    view = TestView()
    
    with app.test_request_context(method='HEAD'):
        if has_head:
            result = view.dispatch_request()
            assert result == "HEAD response"
        elif has_get:
            result = view.dispatch_request()
            assert result == "GET response"
        else:
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
    
    app = flask.Flask(__name__)
    instances = []
    
    class TestView(View):
        init_every_request = init_every_request
        
        def __init__(self):
            instances.append(self)
        
        def dispatch_request(self):
            return "response"
    
    with app.app_context():
        view_func = TestView.as_view(view_name)
        
        for _ in range(num_calls):
            with app.test_request_context():
                view_func()
        
        if init_every_request:
            assert len(instances) == num_calls, f"Expected {num_calls} instances, got {len(instances)}"
            assert len(set(id(inst) for inst in instances)) == num_calls
        else:
            assert len(instances) == 1, f"Expected 1 instance, got {len(instances)}"


@given(
    view_name=valid_python_identifier(),
    class_doc=st.text(min_size=0, max_size=100),
    has_methods=st.booleans()
)
def test_view_function_attribute_preservation(view_name, class_doc, has_methods):
    """Test that generated view function preserves class attributes."""
    
    app = flask.Flask(__name__)
    
    class TestView(View):
        methods = {'GET', 'POST'} if has_methods else None
        provide_automatic_options = False
        
        def dispatch_request(self):
            return "response"
    
    TestView.__doc__ = class_doc
    
    with app.app_context():
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
    
    app = flask.Flask(__name__)
    
    # Create class with method defined in class body
    method_code = f'''
class TestView(MethodView):
    def {method_name}(self):
        return "{method_name} response"
'''
    namespace = {'MethodView': MethodView}
    exec(method_code, namespace)
    TestView = namespace['TestView']
    
    view = TestView()
    
    with app.test_request_context(method=method_name.upper()):
        result = view.dispatch_request()
        assert result == f"{method_name} response"


@given(
    num_args=st.integers(min_value=0, max_value=5),
    num_kwargs=st.integers(min_value=0, max_value=5)
)
def test_view_as_view_argument_forwarding(num_args, num_kwargs):
    """Test that as_view correctly forwards arguments to __init__."""
    
    app = flask.Flask(__name__)
    init_args = []
    init_kwargs = {}
    
    class TestView(View):
        def __init__(self, *args, **kwargs):
            init_args.extend(args)
            init_kwargs.update(kwargs)
        
        def dispatch_request(self):
            return "response"
    
    test_args = [f"arg{i}" for i in range(num_args)]
    test_kwargs = {f"kwarg{i}": f"value{i}" for i in range(num_kwargs)}
    
    with app.app_context():
        view_func = TestView.as_view("test", *test_args, **test_kwargs)
        
        with app.test_request_context():
            view_func()
        
        assert init_args == test_args
        assert init_kwargs == test_kwargs


@given(st.lists(st.sampled_from(list(http_method_funcs)), min_size=1, max_size=3, unique=True))
def test_methodview_methods_attribute_static(methods):
    """Test that MethodView.methods is correctly set for statically defined methods."""
    
    # Create a class with methods defined in the class body
    class_code = "class TestView(MethodView):\n"
    for method in methods:
        class_code += f"    def {method}(self):\n        return '{method}'\n"
    
    namespace = {'MethodView': MethodView}
    exec(class_code, namespace)
    TestView = namespace['TestView']
    
    expected_methods = {m.upper() for m in methods}
    assert TestView.methods == expected_methods, f"Expected {expected_methods}, got {TestView.methods}"