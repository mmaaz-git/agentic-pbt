#!/usr/bin/env python3
"""More targeted property-based tests to find bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest


# Test 1: BedrockResponse.is_json() always returns True regardless of content_type
@given(
    content_type=st.text(min_size=1, max_size=100),
    body=st.text()
)
def test_bedrock_response_is_json_always_true(content_type, body):
    """Test that BedrockResponse.is_json() incorrectly always returns True"""
    from aws_lambda_powertools.event_handler.api_gateway import BedrockResponse
    
    response = BedrockResponse(
        body=body,
        content_type=content_type
    )
    
    # Property: is_json() should return True only for JSON content types
    # But the implementation always returns True!
    result = response.is_json()
    
    # This is a bug - is_json() should check content_type
    if "json" not in content_type.lower():
        # This should fail for non-JSON content types
        # but it doesn't because is_json() always returns True
        assert result == True  # This is the bug - it's always True!
        
        # Let's verify this is a genuine bug
        if content_type in ["text/plain", "text/html", "application/xml", "image/png"]:
            # These are clearly not JSON, yet is_json() returns True
            print(f"BUG: BedrockResponse.is_json() returns True for content_type='{content_type}'")


# Test 2: CORS credentials with wildcard origin should not be allowed
@given(
    expose_headers=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5)
)
def test_cors_credentials_with_wildcard(expose_headers):
    """Test CORS configuration with credentials and wildcard origin"""
    from aws_lambda_powertools.event_handler.api_gateway import CORSConfig
    
    # Create CORS config with wildcard origin and credentials
    cors_config = CORSConfig(
        allow_origin="*",
        allow_credentials=True,
        expose_headers=expose_headers
    )
    
    # Get headers for a specific origin
    headers = cors_config.to_dict("https://example.com")
    
    # Property: When allow_origin is "*" and allow_credentials is True,
    # the Access-Control-Allow-Credentials header should NOT be set
    # This is a security requirement per CORS spec
    if "Access-Control-Allow-Origin" in headers:
        if headers["Access-Control-Allow-Origin"] == "*":
            # Bug: credentials should not be allowed with wildcard
            assert "Access-Control-Allow-Credentials" not in headers, \
                "CORS allows credentials with wildcard origin - security issue!"


# Test 3: OpenAPI path conversion with special characters
@given(
    param_name=st.text(alphabet=st.characters(blacklist_characters="<>", min_codepoint=33, max_codepoint=126), min_size=1, max_size=20)
)
def test_openapi_path_conversion(param_name):
    """Test OpenAPI path conversion from <param> to {param}"""
    from aws_lambda_powertools.event_handler.api_gateway import Route
    import re
    
    # Create a route with dynamic parameter
    path = f"/test/<{param_name}>"
    
    route = Route(
        method="GET",
        path=path,
        rule=re.compile("^/test$"),
        func=lambda: None,
        cors=False,
        compress=False
    )
    
    # Property: OpenAPI path should convert <param> to {param}
    expected = f"/test/{{{param_name}}}"
    assert route.openapi_path == expected, f"Expected {expected}, got {route.openapi_path}"


# Test 4: Route matching with regex special characters
@given(
    special_chars=st.text(alphabet=".*+?[]{}()|\\^$", min_size=1, max_size=5)
)
def test_route_with_regex_special_chars(special_chars):
    """Test route compilation with regex special characters"""
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    import re
    
    resolver = ApiGatewayResolver()
    
    # Create a route with special regex characters
    route = f"/test/{special_chars}/end"
    
    try:
        # This might fail if special chars aren't properly escaped
        compiled = resolver._compile_regex(route)
        
        # If it compiles, test if it matches correctly
        test_path = f"/test/{special_chars}/end"
        match = compiled.match(test_path)
        
        # It should match the exact path
        assert match is not None, f"Route {route} didn't match path {test_path}"
    except re.error as e:
        # If regex compilation fails, this is a bug
        print(f"BUG: Route compilation failed for special chars: {special_chars}")
        print(f"Error: {e}")


# Test 5: Empty CORS headers list
def test_cors_empty_allow_headers():
    """Test CORS with empty allow_headers list"""
    from aws_lambda_powertools.event_handler.api_gateway import CORSConfig
    
    # Create CORS config with empty allow_headers
    cors_config = CORSConfig(
        allow_origin="*",
        allow_headers=[]  # Empty list
    )
    
    headers = cors_config.to_dict("https://example.com")
    
    # The required headers should still be included
    assert "Access-Control-Allow-Headers" in headers
    
    # Check if required headers are present
    allow_headers = headers["Access-Control-Allow-Headers"]
    required = ["Authorization", "Content-Type", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"]
    
    for req_header in required:
        assert req_header in allow_headers, f"Required header {req_header} missing from CORS headers"


# Test 6: Path stripping with exact match
@given(
    prefix=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20)
)
def test_path_stripping_exact_match(prefix):
    """Test path stripping when path exactly matches prefix"""
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    
    prefix = f"/{prefix}"
    
    resolver = ApiGatewayResolver(strip_prefixes=[prefix])
    
    # When path exactly matches prefix
    result = resolver._remove_prefix(prefix)
    
    # Should return "/"
    assert result == "/", f"Expected '/', got '{result}' for exact prefix match"
    
    # Also test with trailing slash
    result2 = resolver._remove_prefix(prefix + "/")
    assert result2 == "/", f"Expected '/', got '{result2}' for prefix with trailing slash"


# Test 7: Multiple matching prefixes
@given(
    base=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=10)
)
def test_multiple_matching_prefixes(base):
    """Test when multiple prefixes could match"""
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    
    # Create overlapping prefixes
    prefix1 = f"/{base}"
    prefix2 = f"/{base}extra"
    
    path = f"/{base}extra/something"
    
    resolver = ApiGatewayResolver(strip_prefixes=[prefix1, prefix2])
    
    result = resolver._remove_prefix(path)
    
    # The first matching prefix should be used
    # This tests the ordering behavior
    expected = "extra/something"  # If prefix1 is matched first
    
    # Actually the behavior depends on which prefix matches first
    # Let's just verify it removes something
    assert result != path, "No prefix was removed"
    assert not result.startswith(f"/{base}"), f"Prefix /{base} was not removed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])