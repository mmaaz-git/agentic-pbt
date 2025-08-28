#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, HealthCheck, note
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize, Bundle
import pyramid.request
from pyramid.request import Request, CallbackMethodsMixin
from pyramid.response import Response
from pyramid.registry import Registry
from pyramid.encode import url_quote, urlencode
from pyramid.url import parse_url_overrides, QUERY_SAFE, ANCHOR_SAFE
from collections import deque
import weakref
import urllib.parse


# Test URL encoding edge cases
@given(
    query=st.one_of(
        st.text(min_size=1),
        st.dictionaries(st.text(min_size=1), st.text()),
        st.dictionaries(st.text(min_size=1), st.lists(st.text(), min_size=1, max_size=3))
    ),
    anchor=st.text()
)
def test_parse_url_overrides_encoding(query, anchor):
    """Test URL parsing with various query and anchor encodings"""
    request = Request.blank('/')
    request.registry = Registry()
    
    kw = {
        '_query': query,
        '_anchor': anchor
    }
    
    app_url, qs, frag = parse_url_overrides(request, kw.copy())
    
    # Properties to check:
    # 1. Query string should start with ? if query is non-empty
    if query:
        assert qs.startswith('?'), f"Query string should start with ?: {qs}"
        
        # If query is dict, it should be URL encoded
        if isinstance(query, dict):
            # Check that the encoding is valid
            parsed = urllib.parse.parse_qs(qs[1:])  # Skip the ?
            # Each key in original dict should be in parsed (though values might be lists)
            for key in query:
                assert key in parsed or urllib.parse.quote(key) in qs, \
                    f"Key {key} missing from parsed query string"
    
    # 2. Anchor should start with # if non-empty
    if anchor:
        assert frag.startswith('#'), f"Fragment should start with #: {frag}"
    
    # 3. Empty strings for empty inputs
    if not query:
        assert qs == '', f"Empty query should produce empty string, got: {qs}"
    if not anchor:
        assert frag == '', f"Empty anchor should produce empty string, got: {frag}"


# Test callback re-entrancy
@given(st.integers(min_value=1, max_value=5))
def test_callback_reentrancy(depth):
    """Test that callbacks can add more callbacks during processing"""
    request = Request.blank('/')
    request.registry = Registry()
    
    call_log = []
    
    def make_reentrant_callback(level):
        def callback(req, resp):
            call_log.append(f"level_{level}")
            if level < depth:
                # Add another callback during processing
                req.add_response_callback(make_reentrant_callback(level + 1))
        return callback
    
    # Add initial callback
    request.add_response_callback(make_reentrant_callback(1))
    
    # Process callbacks
    dummy_response = Response()
    request._process_response_callbacks(dummy_response)
    
    # All levels should have been called
    expected = [f"level_{i}" for i in range(1, depth + 1)]
    assert call_log == expected, f"Expected {expected}, got {call_log}"


# Test URL generation with special characters
@given(
    host=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters=':/?#[]@'), min_size=1, max_size=50),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535).map(str))
)
def test_partial_url_with_special_hosts(host, port):
    """Test URL generation with various host formats"""
    request = Request.blank('/')
    request.environ['wsgi.url_scheme'] = 'http'
    request.environ['SERVER_NAME'] = 'default.com'
    request.environ['SERVER_PORT'] = '80'
    
    try:
        url = request._partial_application_url(host=host, port=port)
        
        # Basic validation - URL should contain the host
        if not ':' in host:  # If host doesn't have port already
            assert host in url or urllib.parse.quote(host) in url, \
                f"Host {host} should be in URL: {url}"
        
        # Port handling
        if port and port not in ['80', '443']:
            assert f':{port}' in url, f"Port {port} should be in URL: {url}"
            
    except (ValueError, TypeError) as e:
        # Some hosts might be invalid - that's OK, just note it
        note(f"Host '{host}' caused exception: {e}")


# Test callback memory leaks with weak references
@given(st.integers(min_value=10, max_value=100))
def test_callback_no_memory_leak(num_callbacks):
    """Test that callbacks don't create memory leaks through circular references"""
    request = Request.blank('/')
    request.registry = Registry()
    
    # Create objects that will be referenced by callbacks
    objects = []
    weak_refs = []
    
    for i in range(num_callbacks):
        obj = object()
        objects.append(obj)
        weak_refs.append(weakref.ref(obj))
        
        # Create callback that captures the object
        def make_callback(captured_obj):
            def callback(req, resp):
                # Reference the captured object
                _ = captured_obj
            return callback
        
        request.add_response_callback(make_callback(obj))
    
    # Clear strong references
    objects.clear()
    
    # Process callbacks to clear them from queue
    dummy_response = Response()
    request._process_response_callbacks(dummy_response)
    
    # After processing, objects should be garbage collectable
    # (weak refs should return None)
    import gc
    gc.collect()
    
    alive_count = sum(1 for ref in weak_refs if ref() is not None)
    # Some objects might still be alive due to Python's GC, but most should be gone
    assert alive_count < num_callbacks // 2, \
        f"Too many objects still alive: {alive_count}/{num_callbacks}"


# Stateful testing for callback queue operations
class CallbackQueueStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.request = Request.blank('/')
        self.request.registry = Registry()
        self.response_callbacks = []
        self.finished_callbacks = []
        self.next_id = 0
    
    @rule()
    def add_response_callback(self):
        """Add a response callback"""
        cb_id = self.next_id
        self.next_id += 1
        
        def callback(req, resp):
            pass  # Just a dummy callback
        
        self.request.add_response_callback(callback)
        self.response_callbacks.append(cb_id)
        note(f"Added response callback {cb_id}")
    
    @rule()
    def add_finished_callback(self):
        """Add a finished callback"""
        cb_id = self.next_id
        self.next_id += 1
        
        def callback(req):
            pass  # Just a dummy callback
        
        self.request.add_finished_callback(callback)
        self.finished_callbacks.append(cb_id)
        note(f"Added finished callback {cb_id}")
    
    @rule()
    def process_response_callbacks(self):
        """Process all response callbacks"""
        if self.response_callbacks:
            dummy_response = Response()
            self.request._process_response_callbacks(dummy_response)
            self.response_callbacks.clear()
            note("Processed response callbacks")
    
    @rule()
    def process_finished_callbacks(self):
        """Process all finished callbacks"""
        if self.finished_callbacks:
            self.request._process_finished_callbacks()
            self.finished_callbacks.clear()
            note("Processed finished callbacks")
    
    @invariant()
    def queue_sizes_match(self):
        """Queue sizes should match our tracking"""
        assert len(self.request.response_callbacks) == len(self.response_callbacks), \
            f"Response queue size mismatch: {len(self.request.response_callbacks)} != {len(self.response_callbacks)}"
        assert len(self.request.finished_callbacks) == len(self.finished_callbacks), \
            f"Finished queue size mismatch: {len(self.request.finished_callbacks)} != {len(self.finished_callbacks)}"


# Test URL generation with IPv6 addresses
@given(
    ipv6=st.sampled_from([
        '::1',
        '2001:db8::1',
        'fe80::1',
        '[::1]',
        '[2001:db8::1]'
    ]),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535).map(str))
)
def test_ipv6_url_generation(ipv6, port):
    """Test URL generation with IPv6 addresses"""
    request = Request.blank('/')
    request.environ['wsgi.url_scheme'] = 'http'
    request.environ['SERVER_NAME'] = 'default.com'
    request.environ['SERVER_PORT'] = '80'
    
    url = request._partial_application_url(host=ipv6, port=port)
    
    # IPv6 addresses should be bracketed in URLs
    if not ipv6.startswith('['):
        assert f'[{ipv6}]' in url or ipv6 in url, \
            f"IPv6 address should be in URL: {url}"
    else:
        assert ipv6 in url, f"Bracketed IPv6 should be in URL: {url}"


# Test edge cases with None and empty values
@given(
    scheme=st.one_of(st.none(), st.just(''), st.just('http'), st.just('https')),
    host=st.one_of(st.none(), st.just(''), st.just('example.com')),
    port=st.one_of(st.none(), st.just(''), st.just('80'), st.just('443'), st.just('8080'))
)
def test_partial_url_empty_values(scheme, host, port):
    """Test URL generation with empty or None values"""
    request = Request.blank('/')
    request.environ['wsgi.url_scheme'] = 'http'
    request.environ['SERVER_NAME'] = 'default.com'
    request.environ['SERVER_PORT'] = '80'
    
    # Remove HTTP_HOST to test fallback behavior
    if 'HTTP_HOST' in request.environ:
        del request.environ['HTTP_HOST']
    
    try:
        url = request._partial_application_url(scheme=scheme, host=host, port=port)
        
        # URL should always be a valid URL format
        assert url.startswith('http://') or url.startswith('https://'), \
            f"URL should start with http:// or https://: {url}"
        
        # URL should have a host part
        assert '://' in url, f"URL should have ://: {url}"
        
    except (ValueError, TypeError, AttributeError) as e:
        # Some combinations might be invalid
        note(f"Combination scheme={scheme}, host={host}, port={port} caused: {e}")


TestCallbackQueueStateMachine = CallbackQueueStateMachine.TestCase

if __name__ == "__main__":
    print("Running edge case tests for pyramid.request...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])