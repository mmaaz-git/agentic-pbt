import math
import sys
from hypothesis import assume, given, strategies as st, settings
import pytest
from flask import Flask
from flask.ctx import _AppCtxGlobals, AppContext, RequestContext


# Strategy for valid attribute names  
valid_attr_names = st.text(
    alphabet=st.characters(categories=("Ll", "Lu", "Nd"), include_characters="_"),
    min_size=1,
    max_size=100
).filter(lambda s: s.isidentifier() and not s.startswith("__"))

# Strategy for any Python values
any_value = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=1000),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(max_size=10), st.integers(), max_size=10)
)


class TestAppCtxGlobals:
    """Test properties of the _AppCtxGlobals namespace object"""
    
    @given(valid_attr_names, any_value)
    def test_setattr_getattr_roundtrip(self, name, value):
        """Property: setattr followed by getattr returns the same value"""
        g = _AppCtxGlobals()
        setattr(g, name, value)
        assert getattr(g, name) == value
    
    @given(valid_attr_names, any_value)
    def test_setattr_contains(self, name, value):
        """Property: After setting an attribute, it should be contained in the object"""
        g = _AppCtxGlobals()
        setattr(g, name, value)
        assert name in g
    
    @given(valid_attr_names, any_value)
    def test_delattr_removes_attribute(self, name, value):
        """Property: delattr removes an attribute that was set"""
        g = _AppCtxGlobals()
        setattr(g, name, value)
        delattr(g, name)
        assert name not in g
        with pytest.raises(AttributeError):
            getattr(g, name)
    
    @given(valid_attr_names)
    def test_delattr_nonexistent_raises(self, name):
        """Property: delattr on nonexistent attribute raises AttributeError"""
        g = _AppCtxGlobals()
        with pytest.raises(AttributeError):
            delattr(g, name)
    
    @given(valid_attr_names, any_value, any_value)
    def test_get_with_default(self, name, value, default):
        """Property: get() returns value if present, default otherwise"""
        g = _AppCtxGlobals()
        
        # Test with missing attribute
        assert g.get(name, default) == default
        
        # Test with present attribute
        setattr(g, name, value)
        assert g.get(name, default) == value
    
    @given(valid_attr_names, any_value)
    def test_pop_removes_and_returns(self, name, value):
        """Property: pop() removes attribute and returns its value"""
        g = _AppCtxGlobals()
        setattr(g, name, value)
        popped = g.pop(name)
        assert popped == value
        assert name not in g
    
    @given(valid_attr_names)
    def test_pop_nonexistent_raises(self, name):
        """Property: pop() on nonexistent key without default raises KeyError"""
        g = _AppCtxGlobals()
        with pytest.raises(KeyError):
            g.pop(name)
    
    @given(valid_attr_names, any_value)
    def test_pop_nonexistent_with_default(self, name, default):
        """Property: pop() with default returns default for missing key"""
        g = _AppCtxGlobals()
        assert g.pop(name, default) == default
    
    @given(valid_attr_names, any_value, any_value)
    def test_setdefault_behavior(self, name, value1, value2):
        """Property: setdefault returns existing value or sets and returns default"""
        g = _AppCtxGlobals()
        
        # First call sets and returns the default
        result1 = g.setdefault(name, value1)
        assert result1 == value1
        assert getattr(g, name) == value1
        
        # Second call returns existing value, doesn't change it
        result2 = g.setdefault(name, value2)
        assert result2 == value1
        assert getattr(g, name) == value1
    
    @given(st.lists(st.tuples(valid_attr_names, any_value), min_size=0, max_size=10))
    def test_iter_returns_all_keys(self, attrs):
        """Property: iter() returns all attribute names"""
        g = _AppCtxGlobals()
        
        # Remove duplicates by converting to dict
        attrs_dict = dict(attrs)
        
        for name, value in attrs_dict.items():
            setattr(g, name, value)
        
        keys = set(iter(g))
        expected_keys = set(attrs_dict.keys())
        assert keys == expected_keys
    
    @given(valid_attr_names)
    def test_getattr_nonexistent_raises(self, name):
        """Property: Getting nonexistent attribute raises AttributeError"""
        g = _AppCtxGlobals()
        with pytest.raises(AttributeError):
            getattr(g, name)


class TestAppContext:
    """Test properties of AppContext"""
    
    @given(st.data())
    def test_push_pop_stack_invariant(self, data):
        """Property: Multiple push/pop operations maintain stack consistency"""
        app = Flask(__name__)
        
        # Generate a sequence of push operations
        num_pushes = data.draw(st.integers(min_value=1, max_value=5))
        contexts = []
        
        for _ in range(num_pushes):
            ctx = app.app_context()
            ctx.push()
            contexts.append(ctx)
        
        # Pop them in reverse order
        for ctx in reversed(contexts):
            ctx.pop()
    
    @given(st.text(min_size=1, max_size=100))
    def test_context_manager_cleanup(self, app_name):
        """Property: Context manager properly cleans up on exit"""
        app = Flask(app_name)
        
        with app.app_context() as ctx:
            assert ctx.app == app
            assert ctx.g is not None
        
        # After exiting, new context should work fine
        with app.app_context() as ctx2:
            assert ctx2.app == app


class TestRequestContext:
    """Test properties of RequestContext"""
    
    @given(st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=0, max_size=100),
        min_size=1,
        max_size=10
    ))
    def test_copy_preserves_request(self, environ_extras):
        """Property: Copying RequestContext preserves the request object"""
        app = Flask(__name__)
        
        # Create a minimal WSGI environ
        environ = {
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'PATH_INFO': '/',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': sys.stdin,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False
        }
        environ.update(environ_extras)
        
        with app.request_context(environ) as ctx:
            copy = ctx.copy()
            assert copy.request is ctx.request
            assert copy.app is ctx.app
            assert copy.request.environ == ctx.request.environ


class TestContextInteractions:
    """Test interactions between different context types"""
    
    @given(valid_attr_names, any_value)
    def test_app_context_g_isolation(self, name, value):
        """Property: Each app context has isolated g namespace"""
        app1 = Flask('app1')
        app2 = Flask('app2')
        
        with app1.app_context() as ctx1:
            setattr(ctx1.g, name, value)
            
            with app2.app_context() as ctx2:
                # app2's g shouldn't have app1's attribute
                assert not hasattr(ctx2.g, name)
                
                # Set different value in app2
                other_value = f"other_{value}" if isinstance(value, str) else -1
                setattr(ctx2.g, name, other_value)
                
                # Values should be different
                assert getattr(ctx1.g, name) == value
                assert getattr(ctx2.g, name) == other_value
    
    @given(st.integers(min_value=1, max_value=5))
    def test_nested_app_contexts(self, depth):
        """Property: Nested app contexts maintain proper stack order"""
        apps = [Flask(f'app_{i}') for i in range(depth)]
        contexts = []
        
        # Push all contexts
        for app in apps:
            ctx = app.app_context()
            ctx.push()
            contexts.append(ctx)
        
        # Pop in reverse order should work correctly
        for ctx in reversed(contexts):
            ctx.pop()