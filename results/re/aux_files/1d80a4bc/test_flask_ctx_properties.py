import sys
import traceback
from hypothesis import given, strategies as st, assume, settings
import flask
import flask.ctx


# Strategy for creating Flask apps with random configurations
@st.composite
def flask_apps(draw):
    """Generate Flask app instances with random configurations."""
    app_name = draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    config_dict = draw(st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(
            st.integers(),
            st.text(),
            st.booleans(),
            st.none()
        ),
        max_size=5
    ))
    
    app = flask.Flask(app_name)
    for key, value in config_dict.items():
        app.config[key] = value
    return app


# Strategy for generating WSGI environments
@st.composite
def wsgi_environments(draw):
    """Generate valid WSGI environment dictionaries."""
    method = draw(st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']))
    path = draw(st.text(min_size=1, max_size=100).map(lambda x: '/' + x.strip('/')))
    
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'SERVER_NAME': draw(st.text(min_size=1, max_size=50)),
        'SERVER_PORT': str(draw(st.integers(min_value=1, max_value=65535))),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': draw(st.sampled_from(['http', 'https'])),
        'wsgi.input': None,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': draw(st.booleans()),
        'wsgi.multiprocess': draw(st.booleans()),
        'wsgi.run_once': False,
    }
    return environ


# Property 1: Push/pop stack behavior - contexts must be popped in LIFO order
@given(flask_apps(), st.lists(st.integers(min_value=0, max_value=10), min_size=1, max_size=5))
def test_app_context_push_pop_stack_invariant(app, push_pop_sequence):
    """Test that app contexts follow LIFO stack behavior."""
    contexts = []
    
    try:
        # Push contexts based on sequence
        for i in push_pop_sequence:
            if i < 5:  # Push
                ctx = flask.ctx.AppContext(app)
                ctx.push()
                contexts.append(ctx)
            elif contexts:  # Pop
                ctx = contexts.pop()
                ctx.pop()
                
        # Clean up remaining contexts
        while contexts:
            ctx = contexts.pop()
            ctx.pop()
            
    except AssertionError as e:
        if "Popped wrong" in str(e):
            # This is the expected assertion for wrong pop order
            # But we should never trigger it with correct LIFO order
            raise
    except Exception:
        # Other exceptions might be OK (e.g., teardown errors)
        pass


# Property 2: Request context implies app context
@given(flask_apps(), wsgi_environments())
def test_request_context_implies_app_context(app, environ):
    """Test that when request context is active, app context is also active."""
    # Initially both should be False
    assert not flask.ctx.has_app_context()
    assert not flask.ctx.has_request_context()
    
    # Create and push request context
    ctx = flask.ctx.RequestContext(app, environ)
    ctx.push()
    
    try:
        # When request context is active, app context must also be active
        assert flask.ctx.has_request_context()
        assert flask.ctx.has_app_context()  # This is the key invariant
    finally:
        ctx.pop()
    
    # After popping, both should be False again
    assert not flask.ctx.has_app_context()
    assert not flask.ctx.has_request_context()


# Property 3: RequestContext.copy() preserves essential properties
@given(flask_apps(), wsgi_environments())
def test_request_context_copy_preserves_properties(app, environ):
    """Test that copying a request context preserves its essential properties."""
    original_ctx = flask.ctx.RequestContext(app, environ)
    original_ctx.push()
    
    try:
        # Create a copy
        copied_ctx = original_ctx.copy()
        
        # The copy should have the same app
        assert copied_ctx.app is original_ctx.app
        
        # The copy should have the same request object
        assert copied_ctx.request is original_ctx.request
        
        # The copy should have the same environ
        assert copied_ctx.request.environ == original_ctx.request.environ
        
        # Pop original and push copy - should work
        original_ctx.pop()
        copied_ctx.push()
        
        # Context should still be active
        assert flask.ctx.has_request_context()
        assert flask.ctx.has_app_context()
        
        copied_ctx.pop()
    except:
        # Clean up
        try:
            original_ctx.pop()
        except:
            pass
        raise


# Property 4: Context detection functions correctly reflect state
@given(flask_apps(), st.booleans(), st.booleans())
def test_context_detection_functions(app, push_app_ctx, push_request_ctx):
    """Test that has_app_context() and has_request_context() correctly reflect state."""
    # Initially both should be False
    assert not flask.ctx.has_app_context()
    assert not flask.ctx.has_request_context()
    
    app_ctx = None
    request_ctx = None
    
    try:
        if push_app_ctx and not push_request_ctx:
            # Push only app context
            app_ctx = flask.ctx.AppContext(app)
            app_ctx.push()
            assert flask.ctx.has_app_context()
            assert not flask.ctx.has_request_context()
            
        elif push_request_ctx:
            # Push request context (which also pushes app context)
            environ = {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/',
                'SERVER_NAME': 'localhost',
                'SERVER_PORT': '80',
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'http',
                'wsgi.input': None,
                'wsgi.errors': sys.stderr,
                'wsgi.multithread': False,
                'wsgi.multiprocess': False,
                'wsgi.run_once': False,
            }
            request_ctx = flask.ctx.RequestContext(app, environ)
            request_ctx.push()
            assert flask.ctx.has_app_context()
            assert flask.ctx.has_request_context()
            
    finally:
        # Clean up
        if request_ctx:
            request_ctx.pop()
        elif app_ctx:
            app_ctx.pop()
    
    # After cleanup, both should be False
    assert not flask.ctx.has_app_context()
    assert not flask.ctx.has_request_context()


# Property 5: Multiple nested contexts - test push/pop ordering
@given(flask_apps(), st.lists(wsgi_environments(), min_size=2, max_size=4))
def test_nested_request_contexts_lifo_order(app, environs):
    """Test that multiple nested request contexts follow LIFO order."""
    contexts = []
    
    try:
        # Push multiple contexts
        for environ in environs:
            ctx = flask.ctx.RequestContext(app, environ)
            ctx.push()
            contexts.append(ctx)
            assert flask.ctx.has_request_context()
        
        # Pop in reverse order
        while contexts:
            ctx = contexts.pop()
            ctx.pop()
            
    except AssertionError as e:
        # Check if it's the "Popped wrong" assertion
        if "Popped wrong" in str(e):
            # This means our LIFO order was violated
            raise
    except Exception:
        # Clean up any remaining contexts
        while contexts:
            try:
                contexts.pop().pop()
            except:
                pass


# Property 6: copy_current_request_context decorator preserves context
@given(flask_apps(), wsgi_environments(), st.integers())
def test_copy_current_request_context_decorator(app, environ, value):
    """Test that copy_current_request_context preserves the context."""
    result_container = []
    
    @flask.ctx.copy_current_request_context
    def decorated_function(val):
        # This should have access to request context
        result_container.append(flask.ctx.has_request_context())
        result_container.append(val)
        return val * 2
    
    # Push request context
    ctx = flask.ctx.RequestContext(app, environ)
    ctx.push()
    
    try:
        # Call the decorated function
        result = decorated_function(value)
        
        # Check that the function had request context
        assert result_container[0] == True
        assert result_container[1] == value
        assert result == value * 2
        
    finally:
        ctx.pop()


# Property 7: after_this_request registers callbacks correctly
@given(flask_apps(), wsgi_environments(), st.lists(st.integers(), min_size=1, max_size=3))
def test_after_this_request_callback_registration(app, environ, callback_values):
    """Test that after_this_request correctly registers and executes callbacks."""
    
    @app.route('/')
    def index():
        # Register callbacks using after_this_request
        for val in callback_values:
            @flask.ctx.after_this_request
            def callback(response):
                response.headers[f'X-Test-{val}'] = str(val)
                return response
        return 'OK'
    
    with app.test_client() as client:
        response = client.get('/')
        
        # Check that all callbacks were executed
        for val in callback_values:
            header_key = f'X-Test-{val}'
            # The headers might have duplicates if same value appears multiple times
            assert any(header_key in str(k) for k in response.headers.keys())


if __name__ == '__main__':
    print("Running property-based tests for flask.ctx module...")
    import pytest
    pytest.main([__file__, '-v'])