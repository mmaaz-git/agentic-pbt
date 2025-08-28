import contextvars
import sys
from hypothesis import assume, given, strategies as st, settings, example
import pytest
from flask import Flask, g, has_app_context, has_request_context
from flask.ctx import _AppCtxGlobals, AppContext, RequestContext, after_this_request


# Strategy for valid attribute names  
valid_attr_names = st.text(
    alphabet=st.characters(categories=("Ll", "Lu", "Nd"), include_characters="_"),
    min_size=1,
    max_size=100
).filter(lambda s: s.isidentifier() and not s.startswith("__"))


class TestAppCtxGlobalsEdgeCases:
    """Test edge cases in _AppCtxGlobals"""
    
    @given(valid_attr_names)
    def test_pop_sentinel_vs_default_none(self, name):
        """Property: pop() with _sentinel vs None default behaves differently"""
        g = _AppCtxGlobals()
        
        # When key doesn't exist, pop with _sentinel raises KeyError
        with pytest.raises(KeyError):
            g.pop(name)
        
        # But pop with None default returns None
        assert g.pop(name, None) is None
    
    @given(valid_attr_names)
    def test_setdefault_with_none(self, name):
        """Property: setdefault with None still sets the attribute"""
        g = _AppCtxGlobals()
        
        result = g.setdefault(name, None)
        assert result is None
        assert name in g
        assert getattr(g, name) is None
    
    @given(st.lists(valid_attr_names, min_size=2, unique=True))
    def test_pop_during_iteration(self, names):
        """Property: Popping during iteration might affect iteration"""
        g = _AppCtxGlobals()
        
        # Set all attributes
        for name in names:
            setattr(g, name, f"value_{name}")
        
        # Try to pop during iteration - this tests dict iteration behavior
        collected = []
        for name in g:
            collected.append(name)
            if len(collected) == 1:
                # Pop a different attribute during iteration
                if len(names) > 1:
                    g.pop(names[-1], None)
        
        # The iteration should complete without error
        assert len(collected) >= len(names) - 1


class TestContextPushPopEdgeCases:
    """Test edge cases in context push/pop operations"""
    
    def test_app_context_pop_wrong_context_assertion(self):
        """Property: Popping wrong app context raises AssertionError"""
        app1 = Flask('app1')
        app2 = Flask('app2')
        
        ctx1 = app1.app_context()
        ctx2 = app2.app_context()
        
        ctx1.push()
        ctx2.push()
        
        # Try to pop ctx1 when ctx2 is on top - should fail
        with pytest.raises(AssertionError, match="Popped wrong app context"):
            ctx1.pop()
        
        # Clean up
        ctx2.pop()
        ctx1.pop()
    
    def test_request_context_pop_wrong_context_assertion(self):
        """Property: Popping wrong request context raises AssertionError"""
        app = Flask('app')
        
        environ1 = {
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'PATH_INFO': '/path1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': sys.stdin,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False
        }
        
        environ2 = environ1.copy()
        environ2['PATH_INFO'] = '/path2'
        
        ctx1 = app.request_context(environ1)
        ctx2 = app.request_context(environ2)
        
        ctx1.push()
        ctx2.push()
        
        # Try to pop ctx1 when ctx2 is on top - should fail
        with pytest.raises(AssertionError, match="Popped wrong request context"):
            ctx1.pop()
        
        # Clean up
        ctx2.pop()
        ctx1.pop()
    
    @given(st.integers(min_value=2, max_value=5))
    def test_multiple_pushes_same_context(self, num_pushes):
        """Property: Same context can be pushed multiple times"""
        app = Flask('app')
        ctx = app.app_context()
        
        # Push same context multiple times
        for _ in range(num_pushes):
            ctx.push()
        
        # Should be able to pop same number of times
        for _ in range(num_pushes):
            ctx.pop()
    
    def test_after_this_request_outside_context(self):
        """Property: after_this_request fails outside request context"""
        
        def dummy_handler(response):
            return response
        
        with pytest.raises(RuntimeError, match="can only be used when a request"):
            after_this_request(dummy_handler)
    
    @given(st.integers(min_value=1, max_value=10))
    def test_after_request_functions_accumulate(self, num_handlers):
        """Property: Multiple after_this_request handlers accumulate"""
        app = Flask('app')
        
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
        
        with app.request_context(environ) as ctx:
            handlers = []
            for i in range(num_handlers):
                def handler(response, i=i):
                    return response
                handlers.append(handler)
                after_this_request(handler)
            
            # Check that all handlers were registered
            assert len(ctx._after_request_functions) == num_handlers


class TestContextVarBehavior:
    """Test behavior with context variables"""
    
    def test_context_locals_not_shared_across_threads(self):
        """Property: Context locals are thread-local"""
        import threading
        import time
        
        app = Flask('app')
        results = {}
        
        def thread_func(thread_id):
            with app.app_context() as ctx:
                ctx.g.thread_id = thread_id
                time.sleep(0.01)  # Allow other threads to run
                results[thread_id] = getattr(ctx.g, 'thread_id', None)
        
        threads = []
        for i in range(3):
            t = threading.Thread(target=thread_func, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Each thread should see its own value
        assert results == {0: 0, 1: 1, 2: 2}
    
    @given(st.integers(min_value=1, max_value=5))
    def test_nested_context_token_management(self, depth):
        """Property: Context tokens are managed correctly in nested contexts"""
        app = Flask('app')
        
        contexts = []
        for i in range(depth):
            ctx = app.app_context()
            ctx.push()
            contexts.append(ctx)
            # Each context should accumulate tokens
            assert len(ctx._cv_tokens) == 1
        
        # Pop in reverse order
        for i, ctx in enumerate(reversed(contexts)):
            ctx.pop()
            # After popping, token list should be empty
            assert len(ctx._cv_tokens) == 0


class TestAppCtxGlobalsSpecialMethods:
    """Test special methods and edge cases in _AppCtxGlobals"""
    
    def test_repr_without_context(self):
        """Property: repr works correctly without app context"""
        g = _AppCtxGlobals()
        repr_str = repr(g)
        assert "object at" in repr_str  # Default object repr
    
    def test_repr_with_context(self):
        """Property: repr shows app name when in context"""
        app = Flask('test_app')
        with app.app_context() as ctx:
            repr_str = repr(ctx.g)
            assert "flask.g of 'test_app'" in repr_str
    
    @given(valid_attr_names)
    def test_contains_vs_hasattr(self, name):
        """Property: __contains__ and hasattr should be consistent"""
        g = _AppCtxGlobals()
        
        # Initially both should be False
        assert (name in g) == hasattr(g, name)
        assert not (name in g)
        
        # After setting, both should be True
        setattr(g, name, "value")
        assert (name in g) == hasattr(g, name)
        assert name in g
        
        # After deleting, both should be False again
        delattr(g, name)
        assert (name in g) == hasattr(g, name)
        assert not (name in g)
    
    def test_dict_attribute_direct_access(self):
        """Property: __dict__ can be accessed directly"""
        g = _AppCtxGlobals()
        
        # Direct dict access should work
        g.__dict__['direct_key'] = 'direct_value'
        assert g.direct_key == 'direct_value'
        assert 'direct_key' in g
        
        # Setting via attribute should update dict
        g.attr_key = 'attr_value'
        assert g.__dict__['attr_key'] == 'attr_value'