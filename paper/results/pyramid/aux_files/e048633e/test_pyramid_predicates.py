#!/usr/bin/env /root/hypothesis-llm/envs/pyramid_env/bin/python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.predicates
from pyramid.predicates import (
    Notted, RequestMethodPredicate, RequestParamPredicate,
    EffectivePrincipalsPredicate, PhysicalPathPredicate,
    HeaderPredicate, PathInfoPredicate, XHRPredicate,
    AcceptPredicate, MatchParamPredicate
)
from unittest.mock import Mock


# Property 1: Notted predicate should invert the result of the underlying predicate
@given(st.booleans())
def test_notted_inverts_predicate(xhr_val):
    """The Notted wrapper should invert the result of the underlying predicate"""
    config = Mock()
    
    # Create a simple XHRPredicate which returns True/False based on request.is_xhr
    xhr_pred = XHRPredicate(xhr_val, config)
    notted_pred = Notted(xhr_pred)
    
    # Mock request with is_xhr matching our test value
    request = Mock()
    request.is_xhr = xhr_val
    context = {}
    
    # The XHR predicate should return True when request.is_xhr matches the expected value
    result = xhr_pred(context, request)
    notted_result = notted_pred(context, request)
    
    # Notted should invert the result
    assert result == (request.is_xhr == xhr_val)
    assert notted_result == (not result)


# Property 2: RequestMethodPredicate - GET should always imply HEAD
@given(st.lists(st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']), min_size=1))
def test_request_method_get_implies_head(methods):
    """When GET is in methods, HEAD should also be accepted"""
    config = Mock()
    pred = RequestMethodPredicate(methods, config)
    
    context = {}
    request = Mock()
    
    # If GET is in the original methods
    if 'GET' in methods:
        # Then HEAD should be accepted by the predicate
        request.method = 'HEAD'
        assert pred(context, request) == True, f"HEAD should be accepted when GET is in {methods}"
    
    # Test that specified methods are accepted
    for method in methods:
        request.method = method
        assert pred(context, request) == True, f"{method} should be accepted"


# Property 3: RequestParamPredicate parsing consistency
@given(st.text(min_size=1).filter(lambda x: '=' not in x and not x.startswith('=')))
def test_request_param_predicate_key_only(key):
    """Parameters without = should check for presence only"""
    config = Mock()
    pred = RequestParamPredicate(key, config)
    
    context = {}
    request = Mock()
    
    # If the key is present (with any value), predicate should return True
    request.params = {key: 'any_value'}
    assert pred(context, request) == True
    
    # If the key is missing, predicate should return False
    request.params = {}
    assert pred(context, request) == False


@given(
    st.text(min_size=1).filter(lambda x: '=' not in x),
    st.text()
)
def test_request_param_predicate_key_value(key, value):
    """Parameters with = should check both key and value"""
    config = Mock()
    param_str = f"{key}={value}"
    pred = RequestParamPredicate(param_str, config)
    
    context = {}
    request = Mock()
    
    # Exact match should return True
    request.params = {key: value}
    assert pred(context, request) == True
    
    # Different value should return False
    if value != 'different':
        request.params = {key: 'different'}
        assert pred(context, request) == False
    
    # Missing key should return False
    request.params = {}
    assert pred(context, request) == False


# Property 4: EffectivePrincipalsPredicate subset checking
@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=10),
    st.lists(st.text(min_size=1), min_size=0, max_size=10)
)
def test_effective_principals_subset_property(required_principals, request_principals):
    """Predicate should return True iff required principals are subset of request principals"""
    config = Mock()
    pred = EffectivePrincipalsPredicate(required_principals, config)
    
    context = {}
    request = Mock()
    request.effective_principals = request_principals
    
    result = pred(context, request)
    expected = set(required_principals).issubset(set(request_principals))
    
    assert result == expected, f"Required {required_principals} subset of {request_principals}: expected {expected}, got {result}"


# Property 5: PhysicalPathPredicate handles both string and tuple inputs
@given(st.lists(st.text(min_size=1).filter(lambda x: '/' not in x), min_size=0, max_size=5))
def test_physical_path_string_tuple_equivalence(path_parts):
    """String path and tuple path should be handled consistently"""
    config = Mock()
    
    # Create path as string
    if path_parts:
        string_path = '/' + '/'.join(path_parts)
    else:
        string_path = '/'
    
    # Create path as tuple (with leading empty string)
    tuple_path = ('',) + tuple(path_parts)
    
    # Both should create equivalent predicates
    string_pred = PhysicalPathPredicate(string_path, config)
    tuple_pred = PhysicalPathPredicate(tuple_path, config)
    
    # They should have the same internal value
    assert string_pred.val == tuple_pred.val, f"String {string_path} and tuple {tuple_path} should produce same internal value"
    
    # They should produce the same text representation
    assert string_pred.text() == tuple_pred.text()


# Property 6: Text and phash methods should be idempotent
@given(st.sampled_from(['GET', 'POST', 'PUT']))
def test_text_phash_idempotence(method):
    """text() and phash() should return the same value when called multiple times"""
    config = Mock()
    pred = RequestMethodPredicate(method, config)
    
    # Call text() multiple times
    text1 = pred.text()
    text2 = pred.text()
    text3 = pred.text()
    assert text1 == text2 == text3, "text() should be idempotent"
    
    # Call phash multiple times (it's an alias to text in many cases)
    phash1 = pred.phash()
    phash2 = pred.phash()
    phash3 = pred.phash()
    assert phash1 == phash2 == phash3, "phash() should be idempotent"


# Property 7: HeaderPredicate regex parsing
@given(st.text(min_size=1).filter(lambda x: ':' not in x))
def test_header_predicate_no_colon(header_name):
    """Headers without colon should check for presence only"""
    config = Mock()
    pred = HeaderPredicate(header_name, config)
    
    context = {}
    request = Mock()
    
    # If header is present, should return True
    request.headers = {header_name: 'any_value'}
    assert pred(context, request) == True
    
    # If header is missing, should return False  
    request.headers = {}
    assert pred(context, request) == False


# Property 8: AcceptPredicate with multiple values
@given(st.lists(st.sampled_from(['text/html', 'application/json', 'text/plain', '*/*']), min_size=1, max_size=5))
def test_accept_predicate_multiple_values(accept_values):
    """AcceptPredicate should handle multiple accept values"""
    config = Mock()
    
    # Test both single value and list of values
    for values in [accept_values[0], accept_values]:
        pred = AcceptPredicate(values, config)
        
        # The values should be stored as a tuple
        if not isinstance(values, (list, tuple)):
            assert pred.values == (values,)
        else:
            assert pred.values == tuple(values)
        
        # text() should produce consistent output
        text = pred.text()
        assert 'accept = ' in text


# Property 9: MatchParamPredicate parsing
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda x: '=' not in x),
            st.text()
        ),
        min_size=1,
        max_size=3
    )
)
def test_match_param_predicate_parsing(params):
    """MatchParamPredicate should correctly parse key=value pairs"""
    config = Mock()
    
    # Create param strings
    param_strings = [f"{k}={v}" for k, v in params]
    pred = MatchParamPredicate(param_strings, config)
    
    context = {}
    request = Mock()
    
    # With all matching params, should return True
    request.matchdict = {k: v for k, v in params}
    assert pred(context, request) == True
    
    # With missing matchdict, should return False
    request.matchdict = None
    assert pred(context, request) == False
    
    # With empty matchdict, should return False (if params is not empty)
    request.matchdict = {}
    assert pred(context, request) == False


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])