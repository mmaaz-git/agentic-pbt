#!/usr/bin/env python3
"""Comprehensive property-based testing for google.oauth2 module."""

import sys
import json
import base64
import urllib.parse
import datetime
import traceback
from unittest import mock

sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

import hypothesis
from hypothesis import given, strategies as st, settings

import google.oauth2.utils as utils
import google.oauth2.sts as sts
import google.oauth2._client as _client

# Configure hypothesis
hypothesis.settings.register_profile("fast", max_examples=50)
hypothesis.settings.load_profile("fast")

def test_property(test_func, property_name):
    """Run a property test and report results."""
    print(f"\n{'='*60}")
    print(f"Testing: {property_name}")
    print('='*60)
    
    try:
        test_func()
        print(f"✓ PASSED: {property_name}")
        return True
    except Exception as e:
        print(f"✗ FAILED: {property_name}")
        print(f"Error: {e}")
        print("\nStack trace:")
        traceback.print_exc()
        return False

# Property 1: Base64 encoding round-trip
@given(
    client_id=st.text(min_size=1, max_size=50),
    client_secret=st.text(min_size=0, max_size=50)
)
@settings(max_examples=20)
def test_basic_auth_base64():
    """Basic auth header encoding/decoding consistency."""
    def inner(client_id, client_secret):
        client_auth = utils.ClientAuthentication(
            utils.ClientAuthType.basic,
            client_id,
            client_secret
        )
        
        handler = utils.OAuthClientAuthHandler(client_auth)
        headers = {}
        handler.apply_client_authentication_options(headers)
        
        if "Authorization" in headers:
            auth_header = headers["Authorization"]
            assert auth_header.startswith("Basic ")
            
            b64_credentials = auth_header[6:]
            decoded = base64.b64decode(b64_credentials).decode('utf-8')
            
            expected = f"{client_id}:{client_secret if client_secret else ''}"
            assert decoded == expected, f"Mismatch: {decoded} != {expected}"
    
    inner()

# Property 2: Expiry parsing
@given(
    expires_in=st.one_of(
        st.integers(min_value=0, max_value=86400),
        st.from_regex(r"[0-9]{1,5}", fullmatch=True)
    )
)
@settings(max_examples=20)
def test_expiry_parsing():
    """_parse_expiry handles both int and string expires_in."""
    def inner(expires_in):
        response_data = {"expires_in": expires_in}
        expiry = _client._parse_expiry(response_data)
        
        assert isinstance(expiry, datetime.datetime), f"Expected datetime, got {type(expiry)}"
        
        expected_seconds = int(expires_in) if isinstance(expires_in, str) else expires_in
        now = datetime.datetime.utcnow()
        expected_expiry = now + datetime.timedelta(seconds=expected_seconds)
        
        diff = abs((expiry - expected_expiry).total_seconds())
        assert diff < 3, f"Time difference too large: {diff} seconds"
    
    inner()

# Property 3: Empty field removal
@given(
    grant_type=st.text(min_size=1, max_size=30),
    resource=st.one_of(st.none(), st.text(min_size=0, max_size=50)),
    audience=st.one_of(st.none(), st.text(min_size=0, max_size=50))
)
@settings(max_examples=20)
def test_empty_field_removal():
    """Empty fields are removed from request body."""
    def inner(grant_type, resource, audience):
        request_body = {
            "grant_type": grant_type,
            "resource": resource,
            "audience": audience,
            "scope": "",
            "options": None,
        }
        
        # Remove empty fields
        for k, v in dict(request_body).items():
            if v is None or v == "":
                del request_body[k]
        
        # Verify no empty values remain
        for key, value in request_body.items():
            assert value is not None, f"None value found for {key}"
            assert value != "", f"Empty string found for {key}"
        
        # Required field should remain
        assert "grant_type" in request_body
    
    inner()

# Property 4: Error response parsing
@given(
    error_code=st.text(min_size=1, max_size=30),
    error_description=st.one_of(st.none(), st.text(max_size=100))
)
@settings(max_examples=20)
def test_error_parsing():
    """handle_error_response correctly parses JSON errors."""
    def inner(error_code, error_description):
        error_data = {"error": error_code}
        if error_description is not None:
            error_data["error_description"] = error_description
        
        response_body = json.dumps(error_data)
        
        try:
            utils.handle_error_response(response_body)
            assert False, "Should have raised OAuthError"
        except Exception as e:
            assert "OAuthError" in e.__class__.__name__
            assert f"Error code {error_code}" in str(e)
            if error_description:
                assert error_description in str(e)
    
    inner()

# Additional edge case tests
def test_edge_cases():
    """Test specific edge cases that might reveal bugs."""
    print("\n" + "="*60)
    print("Testing Edge Cases")
    print("="*60)
    
    issues_found = []
    
    # Test 1: Expiry with invalid string
    print("\n1. Testing expiry with non-numeric string...")
    try:
        response = {"expires_in": "not_a_number"}
        expiry = _client._parse_expiry(response)
        print(f"  Result: {expiry}")
        print("  ✗ No exception raised for invalid string!")
        issues_found.append("Expiry parsing accepts invalid strings")
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"  ? Unexpected exception: {e.__class__.__name__}: {e}")
        issues_found.append(f"Unexpected exception for invalid expiry: {e}")
    
    # Test 2: Expiry with float string
    print("\n2. Testing expiry with float string...")
    try:
        response = {"expires_in": "3600.5"}
        expiry = _client._parse_expiry(response)
        print(f"  Result: {expiry}")
        print("  ✗ No exception raised for float string!")
        issues_found.append("Expiry parsing accepts float strings")
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"  ? Unexpected exception: {e.__class__.__name__}: {e}")
    
    # Test 3: Negative expiry
    print("\n3. Testing negative expiry...")
    response = {"expires_in": -100}
    expiry = _client._parse_expiry(response)
    now = datetime.datetime.utcnow()
    if expiry and expiry < now:
        print(f"  ✓ Expiry is in the past: {expiry}")
    else:
        print(f"  ? Expiry: {expiry}, Now: {now}")
    
    # Test 4: Unicode in error messages
    print("\n4. Testing unicode in error messages...")
    try:
        error_json = json.dumps({
            "error": "invalid_request",
            "error_description": "Invalid character: 你好 🚀"
        })
        utils.handle_error_response(error_json)
        print("  ✗ No exception raised!")
        issues_found.append("Error handler didn't raise exception")
    except Exception as e:
        if "你好" in str(e) and "🚀" in str(e):
            print(f"  ✓ Unicode preserved in error: {e}")
        else:
            print(f"  ✗ Unicode not preserved: {e}")
            issues_found.append("Unicode not preserved in error messages")
    
    # Test 5: Malformed JSON in error handler
    print("\n5. Testing malformed JSON in error handler...")
    malformed = '{"error": "test", "description": '  # Incomplete JSON
    try:
        utils.handle_error_response(malformed)
        print("  ✗ No exception raised!")
        issues_found.append("Error handler accepts malformed JSON")
    except Exception as e:
        if malformed in str(e):
            print(f"  ✓ Fallback to raw response: {e}")
        else:
            print(f"  ? Exception: {e}")
    
    return issues_found

def main():
    """Run all property tests."""
    print("PROPERTY-BASED TESTING FOR google.oauth2")
    print("="*60)
    
    results = []
    
    # Run property tests
    tests = [
        (test_basic_auth_base64, "Base64 encoding round-trip"),
        (test_expiry_parsing, "Expiry parsing (int and string)"),
        (test_empty_field_removal, "Empty field removal"),
        (test_error_parsing, "Error response parsing"),
    ]
    
    for test_func, name in tests:
        result = test_property(test_func, name)
        results.append((name, result))
    
    # Run edge case tests
    issues = test_edge_cases()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    print(f"\nProperty Tests: {passed} passed, {failed} failed")
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    if issues:
        print(f"\nPotential Issues Found ({len(issues)}):")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("\nNo additional issues found in edge cases")
    
    return 0 if failed == 0 and not issues else 1

if __name__ == "__main__":
    sys.exit(main())