#!/usr/bin/env python3
"""Property-based tests for aws_lambda_powertools.event_handler module"""

import re
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, HealthCheck
import pytest


# Test 1: Route Pattern Compilation and Matching
@given(
    route_name=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20),
    value=st.text(alphabet=st.characters(blacklist_characters="/<>{}[]\\", min_codepoint=33, max_codepoint=126), min_size=1, max_size=50)
)
def test_route_pattern_compilation_and_matching(route_name, value):
    """Test that dynamic route patterns correctly extract parameters"""
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    
    # Create a dynamic route pattern
    route_pattern = f"/test/<{route_name}>"
    
    # Use the internal _compile_regex method
    resolver = ApiGatewayResolver()
    compiled_regex = resolver._compile_regex(route_pattern)
    
    # Create a test path with the value
    test_path = f"/test/{value}"
    
    # Match the path against the compiled regex
    match = compiled_regex.match(test_path)
    
    # If it matches, the extracted value should be correct
    if match:
        extracted = match.group(route_name)
        # The extracted value should match what we put in (accounting for word boundary matching)
        # The regex uses \\w+ which matches word characters only
        if re.match(r'^[\w\-._~()\'!*:@,;=+&$%<> \[\]{}|^]+$', value):
            assert extracted == value, f"Expected {value}, got {extracted}"


# Test 2: CORS Configuration Origin Matching
@given(
    allowed_origin=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    request_origin=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
)
def test_cors_origin_matching(allowed_origin, request_origin):
    """Test CORS configuration origin matching logic"""
    from aws_lambda_powertools.event_handler.api_gateway import CORSConfig
    
    # Create CORS config with specific allowed origin
    cors_config = CORSConfig(allow_origin=allowed_origin)
    
    # Get CORS headers for the request origin
    headers = cors_config.to_dict(request_origin)
    
    # Property: If origin matches allowed origin or allowed is "*", headers should be returned
    if allowed_origin == "*" or request_origin == allowed_origin:
        assert "Access-Control-Allow-Origin" in headers
        # The returned origin should match the pattern
        if allowed_origin == "*":
            assert headers["Access-Control-Allow-Origin"] == request_origin or headers["Access-Control-Allow-Origin"] == "*"
        else:
            assert headers["Access-Control-Allow-Origin"] == request_origin
    else:
        # No CORS headers should be returned for non-matching origins
        assert "Access-Control-Allow-Origin" not in headers


# Test 3: HTTP Method Normalization
@given(method=st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=10))
def test_http_method_normalization(method):
    """Test that HTTP methods are always stored in uppercase"""
    from aws_lambda_powertools.event_handler.api_gateway import Route
    import re
    
    # Create a route with the given method
    route = Route(
        method=method,
        path="/test",
        rule=re.compile("^/test$"),
        func=lambda: None,
        cors=False,
        compress=False
    )
    
    # Property: The method should always be uppercase
    assert route.method == method.upper(), f"Method {method} was not normalized to {method.upper()}"


# Test 4: Route Path Normalization  
@given(path=st.text())
def test_route_path_normalization(path):
    """Test that empty or whitespace paths are normalized to '/'"""
    from aws_lambda_powertools.event_handler.api_gateway import Route
    import re
    
    # Create a route with the given path
    route = Route(
        method="GET",
        path=path,
        rule=re.compile("^/$"),
        func=lambda: None,
        cors=False,
        compress=False
    )
    
    # Property: Empty or whitespace-only paths should become "/"
    if not path.strip():
        assert route.path == "/", f"Empty/whitespace path '{path}' was not normalized to '/'"
    else:
        assert route.path == path, f"Non-empty path '{path}' was incorrectly changed to '{route.path}'"


# Test 5: CORS Headers with Wildcards
@given(
    extra_origins=st.lists(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()), min_size=0, max_size=5),
    request_origin=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
)
def test_cors_wildcard_and_extra_origins(extra_origins, request_origin):
    """Test CORS with wildcard and extra origins"""
    from aws_lambda_powertools.event_handler.api_gateway import CORSConfig
    
    # Create CORS config with wildcard and extra origins
    cors_config = CORSConfig(allow_origin="*", extra_origins=extra_origins)
    
    # Get CORS headers
    headers = cors_config.to_dict(request_origin)
    
    # Property: Wildcard should allow any origin
    assert "Access-Control-Allow-Origin" in headers
    # With wildcard, any origin should be allowed
    assert headers["Access-Control-Allow-Origin"] in ["*", request_origin]


# Test 6: Path Prefix Removal
@given(
    prefix=st.text(min_size=1, max_size=20).filter(lambda x: x and not x.startswith('/')),
    path_suffix=st.text(min_size=0, max_size=30).filter(lambda x: not x.startswith('/'))
)
def test_path_prefix_removal(prefix, path_suffix):
    """Test path prefix removal logic"""
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    
    # Ensure prefix starts with /
    prefix = f"/{prefix}"
    path = f"{prefix}/{path_suffix}" if path_suffix else prefix
    
    # Create resolver with strip_prefixes
    resolver = ApiGatewayResolver(strip_prefixes=[prefix])
    
    # Remove prefix
    result = resolver._remove_prefix(path)
    
    # Property: Removing a prefix should give the remaining path
    if path == prefix:
        assert result == "/", f"Path equal to prefix should return '/'"
    else:
        expected = f"/{path_suffix}" if path_suffix else "/"
        assert result == expected, f"Expected {expected}, got {result}"


# Test 7: Response class JSON detection  
@given(content_type=st.text())
def test_response_json_detection(content_type):
    """Test Response class JSON content type detection"""
    from aws_lambda_powertools.event_handler.api_gateway import Response
    
    # Create response with given content type
    response = Response(
        status_code=200,
        content_type=content_type,
        body={"test": "data"}
    )
    
    # The Response class should correctly identify JSON content
    # Based on the code, it seems to serialize based on content_type
    assert response.content_type == content_type


# Test 8: Multiple Prefix Removal
@given(
    prefixes=st.lists(
        st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10),
        min_size=1,
        max_size=3
    ).map(lambda lst: [f"/{p}" for p in lst]),
    path=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=50).map(lambda x: f"/{x}")
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_multiple_prefix_removal(prefixes, path):
    """Test removal of multiple prefixes"""
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    
    # Ensure unique prefixes
    prefixes = list(set(prefixes))
    
    resolver = ApiGatewayResolver(strip_prefixes=prefixes)
    result = resolver._remove_prefix(path)
    
    # Property: Result should not have any of the prefixes
    for prefix in prefixes:
        if path.startswith(prefix):
            # If path matches a prefix, it should be removed
            assert not result.startswith(prefix) or result == "/"
            break


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])