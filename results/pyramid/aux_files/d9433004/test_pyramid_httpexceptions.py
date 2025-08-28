"""Property-based tests for pyramid.httpexceptions module"""

import sys
import json
import inspect
from string import Template

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.httpexceptions as httpexc
from hypothesis import given, strategies as st, assume, settings
import pytest

# Get all valid status codes from the status_map
VALID_STATUS_CODES = list(httpexc.status_map.keys())

# Get all exception classes
ALL_EXCEPTION_CLASSES = [
    obj for name, obj in inspect.getmembers(httpexc)
    if inspect.isclass(obj) and issubclass(obj, httpexc.HTTPException) 
    and name.startswith('HTTP') and hasattr(obj, 'code')
]

# Get redirect classes that require location
REDIRECT_CLASSES = [
    obj for name, obj in inspect.getmembers(httpexc)
    if inspect.isclass(obj) and issubclass(obj, httpexc._HTTPMove)
]


# Test 1: exception_response round-trip property
@given(st.sampled_from(VALID_STATUS_CODES))
def test_exception_response_round_trip(status_code):
    """exception_response(code) should create an exception with that exact code"""
    exc = httpexc.exception_response(status_code)
    assert exc.code == status_code
    assert isinstance(exc, httpexc.HTTPException)
    # The exception should be of the correct type from status_map
    expected_class = httpexc.status_map[status_code]
    assert isinstance(exc, expected_class)


# Test 2: exception_response with custom detail
@given(
    st.sampled_from(VALID_STATUS_CODES),
    st.text(min_size=1, max_size=100)
)
def test_exception_response_preserves_detail(status_code, detail):
    """exception_response should preserve the detail argument"""
    exc = httpexc.exception_response(status_code, detail=detail)
    assert exc.detail == detail
    assert exc.message == detail  # message should equal detail per code


# Test 3: HTTPMove subclasses require non-None location
@given(st.sampled_from(REDIRECT_CLASSES))
def test_httpmove_requires_location(redirect_class):
    """All HTTPMove subclasses should raise ValueError when location is None"""
    with pytest.raises(ValueError, match="HTTP redirects need a location"):
        redirect_class(location=None)


# Test 4: HTTPMove subclasses accept and preserve location
@given(
    st.sampled_from(REDIRECT_CLASSES),
    st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
)
def test_httpmove_preserves_location(redirect_class, location):
    """HTTPMove subclasses should preserve the location parameter"""
    exc = redirect_class(location=location)
    assert 'Location' in exc.headers
    assert exc.headers['Location'] == location


# Test 5: String representation property
@given(
    st.sampled_from(ALL_EXCEPTION_CLASSES),
    st.one_of(st.none(), st.text(min_size=0, max_size=100))
)
def test_string_representation(exception_class, detail):
    """str(exception) should return detail if present, otherwise explanation"""
    if issubclass(exception_class, httpexc._HTTPMove):
        exc = exception_class(location='http://example.com', detail=detail)
    else:
        exc = exception_class(detail=detail)
    
    result = str(exc)
    if detail:
        assert result == detail
    else:
        # Should return explanation when detail is None or empty
        assert result == exception_class.explanation


# Test 6: Status format property
@given(st.sampled_from(ALL_EXCEPTION_CLASSES))
def test_status_format(exception_class):
    """Exception status should be formatted as '{code} {title}'"""
    if issubclass(exception_class, httpexc._HTTPMove):
        exc = exception_class(location='http://example.com')
    else:
        exc = exception_class()
    
    expected_status = f"{exc.code} {exc.title}"
    assert exc.status == expected_status


# Test 7: Headers extension property
@given(
    st.sampled_from(ALL_EXCEPTION_CLASSES),
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
            st.text(min_size=0, max_size=100)
        ),
        min_size=1,
        max_size=5
    )
)
def test_headers_extension(exception_class, headers):
    """Headers passed to constructor should be added to response headers"""
    if issubclass(exception_class, httpexc._HTTPMove):
        exc = exception_class(location='http://example.com', headers=headers)
    else:
        exc = exception_class(headers=headers)
    
    for key, value in headers:
        assert key in exc.headers
        # The last value for each key should be preserved
        header_values = exc.headers.getall(key)
        assert value in header_values


# Test 8: JSON formatter property
@given(
    st.sampled_from(ALL_EXCEPTION_CLASSES),
    st.text(min_size=0, max_size=100)
)
def test_json_formatter_validity(exception_class, detail):
    """_json_formatter should produce valid JSON-serializable dictionaries"""
    if issubclass(exception_class, httpexc._HTTPMove):
        exc = exception_class(location='http://example.com', detail=detail)
    else:
        exc = exception_class(detail=detail)
    
    # Call the _json_formatter
    body = str(exc) if exc.detail else exc.explanation
    result = exc._json_formatter(
        status=exc.status,
        body=body,
        title=exc.title,
        environ={}
    )
    
    # Result should be JSON-serializable
    json_str = json.dumps(result)
    assert isinstance(json_str, str)
    
    # Result should contain expected keys
    assert 'message' in result
    assert 'code' in result
    assert 'title' in result
    assert result['title'] == exc.title
    assert result['code'] == exc.status


# Test 9: Body template substitution
@given(
    st.sampled_from(ALL_EXCEPTION_CLASSES),
    st.text(min_size=1, max_size=50)
)  
def test_body_template_is_valid_template(exception_class, detail):
    """body_template_obj should be a valid Template that can be substituted"""
    if issubclass(exception_class, httpexc._HTTPMove):
        exc = exception_class(location='http://example.com', detail=detail)
    else:
        exc = exception_class(detail=detail)
    
    # body_template_obj should be a Template
    assert isinstance(exc.body_template_obj, Template)
    
    # Should be able to substitute without errors
    try:
        result = exc.body_template_obj.substitute(
            explanation=exc.explanation,
            detail=detail or '',
            html_comment='',
            br='<br/>',
            location='http://example.com' if issubclass(exception_class, httpexc._HTTPMove) else ''
        )
        assert isinstance(result, str)
    except KeyError as e:
        pytest.fail(f"Template substitution failed with KeyError: {e}")


# Test 10: Exception inheritance property
@given(st.sampled_from(ALL_EXCEPTION_CLASSES))
def test_exception_inheritance(exception_class):
    """All HTTP exceptions should inherit from both Response and Exception"""
    if issubclass(exception_class, httpexc._HTTPMove):
        exc = exception_class(location='http://example.com')
    else:
        exc = exception_class()
    
    # Should be both a Response and an Exception
    from pyramid.response import Response
    assert isinstance(exc, Response)
    assert isinstance(exc, Exception)
    assert isinstance(exc, httpexc.HTTPException)


# Test 11: Empty body flag for specific status codes
@given(st.sampled_from([204, 304]))  # No Content and Not Modified
def test_empty_body_exceptions(status_code):
    """204 No Content and 304 Not Modified should have empty_body=True"""
    exc = httpexc.exception_response(status_code)
    assert exc.empty_body == True
    # These should not have content-type or content-length headers
    assert 'Content-Type' not in exc.headers
    assert 'Content-Length' not in exc.headers


# Test 12: Exception response view compatibility
@given(
    st.sampled_from(ALL_EXCEPTION_CLASSES),
    st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x.upper() == x),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=5
    )
)
def test_prepare_method_with_environ(exception_class, environ_extra):
    """prepare() method should handle various environ dicts without crashing"""
    if issubclass(exception_class, httpexc._HTTPMove):
        exc = exception_class(location='http://example.com')
    else:
        exc = exception_class()
    
    # Create a minimal WSGI environ
    environ = {
        'REQUEST_METHOD': 'GET',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'PATH_INFO': '/',
    }
    environ.update(environ_extra)
    
    # prepare() should not crash
    exc.prepare(environ)
    assert exc.status  # Should still have a status after prepare


if __name__ == '__main__':
    print("Running property-based tests for pyramid.httpexceptions...")
    pytest.main([__file__, '-v'])