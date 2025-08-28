import string

import flask
from flask.views import MethodView, View
from hypothesis import given, strategies as st


@st.composite
def valid_python_identifier(draw):
    first_char = draw(st.sampled_from(string.ascii_letters + "_"))
    rest = draw(st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=0, max_size=20))
    return first_char + rest


@given(
    view_name=valid_python_identifier(),
    should_init_every=st.booleans(),
    num_calls=st.integers(min_value=2, max_value=10)
)
def test_view_init_every_request_behavior(view_name, should_init_every, num_calls):
    """Test that init_every_request controls instance reuse correctly."""
    
    app = flask.Flask(__name__)
    instances = []
    
    class TestView(View):
        init_every_request = should_init_every
        
        def __init__(self):
            instances.append(self)
        
        def dispatch_request(self):
            return "response"
    
    with app.app_context():
        view_func = TestView.as_view(view_name)
        
        for _ in range(num_calls):
            with app.test_request_context():
                view_func()
        
        if should_init_every:
            assert len(instances) == num_calls, f"Expected {num_calls} instances, got {len(instances)}"
            assert len(set(id(inst) for inst in instances)) == num_calls
        else:
            assert len(instances) == 1, f"Expected 1 instance, got {len(instances)}"


@given(
    view_name=valid_python_identifier(),
    url_param_count=st.integers(min_value=0, max_value=5)
)
def test_view_dispatch_request_kwargs_passing(view_name, url_param_count):
    """Test that URL parameters are correctly passed to dispatch_request."""
    
    app = flask.Flask(__name__)
    received_kwargs = {}
    
    class TestView(View):
        def dispatch_request(self, **kwargs):
            received_kwargs.update(kwargs)
            return "response"
    
    # Generate test kwargs
    test_kwargs = {f"param{i}": f"value{i}" for i in range(url_param_count)}
    
    with app.app_context():
        view_func = TestView.as_view(view_name)
        
        with app.test_request_context():
            view_func(**test_kwargs)
        
        assert received_kwargs == test_kwargs


@given(
    unsupported_method=st.sampled_from(['CONNECT', 'CUSTOM', 'INVALID'])
)
def test_methodview_unsupported_method_error(unsupported_method):
    """Test that MethodView raises proper error for unsupported methods."""
    
    app = flask.Flask(__name__)
    
    class TestView(MethodView):
        def get(self):
            return "GET response"
    
    view = TestView()
    
    with app.test_request_context(method=unsupported_method):
        try:
            view.dispatch_request()
            assert False, "Should have raised AssertionError"
        except AssertionError as e:
            assert f"Unimplemented method {unsupported_method!r}" in str(e)


@given(
    method_with_args=st.sampled_from(['get', 'post']),
    num_kwargs=st.integers(min_value=1, max_value=3)
)
def test_methodview_kwargs_forwarding(method_with_args, num_kwargs):
    """Test that MethodView correctly forwards kwargs to method handlers."""
    
    app = flask.Flask(__name__)
    received_kwargs = {}
    
    class TestView(MethodView):
        def get(self, **kwargs):
            received_kwargs.update(kwargs)
            return "GET"
        
        def post(self, **kwargs):
            received_kwargs.update(kwargs)
            return "POST"
    
    view = TestView()
    test_kwargs = {f"param{i}": f"value{i}" for i in range(num_kwargs)}
    
    with app.test_request_context(method=method_with_args.upper()):
        view.dispatch_request(**test_kwargs)
        assert received_kwargs == test_kwargs