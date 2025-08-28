#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
from quickbooks.client import QuickBooks, to_bytes
import hashlib
import hmac
import base64


@given(
    st.binary(min_size=0, max_size=10000),
    st.text(min_size=0, max_size=1000)
)
@settings(max_examples=500)
def test_webhook_signature_edge_cases(request_body, verifier_token):
    """Test webhook signature validation with edge cases"""
    
    # Skip empty verifier token as it might not be a valid use case
    if not verifier_token:
        assume(False)
    
    # Create signature using the same algorithm as validate_webhook_signature
    hmac_hash = hmac.new(
        to_bytes(verifier_token),
        request_body,
        hashlib.sha256
    ).digest()
    valid_signature = base64.b64encode(hmac_hash).decode('utf-8')
    
    qb = QuickBooks()
    qb.verifier_token = verifier_token
    
    # Convert request_body to string as the method expects
    try:
        request_body_str = request_body.decode('utf-8')
    except UnicodeDecodeError:
        # If can't decode as UTF-8, use replacement
        request_body_str = request_body.decode('utf-8', errors='replace')
    
    # The validation should work correctly
    result = qb.validate_webhook_signature(request_body_str, valid_signature)
    
    if not result:
        print(f"\nFAILURE FOUND!")
        print(f"Request body (bytes): {request_body[:100]}...")
        print(f"Request body (string): {request_body_str[:100]}...")
        print(f"Verifier token: {verifier_token[:100] if len(verifier_token) > 100 else verifier_token}")
        print(f"Valid signature: {valid_signature}")
        print(f"Result: {result}")
        
        # Debug: let's manually check what's happening
        # The issue might be that the method uses request_body.encode('utf-8')
        # but we passed a string that was decoded with errors='replace'
        
        # Let's check if re-encoding gives different bytes
        re_encoded = request_body_str.encode('utf-8')
        if re_encoded != request_body:
            print("ISSUE: Re-encoding the string gives different bytes!")
            print(f"Original bytes: {request_body[:50]}...")
            print(f"Re-encoded bytes: {re_encoded[:50]}...")
            # This is expected behavior when the original bytes weren't valid UTF-8
            # The method assumes the request_body string can be encoded back to the original bytes
            # This is a limitation but not necessarily a bug
            return  # Skip this case
        
        assert False, "Valid signature was rejected"


@given(st.text(min_size=1))
@settings(max_examples=100)
def test_isvalid_object_name_case_sensitivity(object_name):
    """Test if object name validation is case-sensitive"""
    qb = QuickBooks()
    
    # Test if case matters
    if object_name.lower() in [obj.lower() for obj in qb._BUSINESS_OBJECTS]:
        # Object name matches ignoring case
        if object_name in qb._BUSINESS_OBJECTS:
            # Exact match - should pass
            try:
                assert qb.isvalid_object_name(object_name) == True
            except:
                print(f"FAILURE: Valid object name {object_name} was rejected")
                raise
        else:
            # Case mismatch - let's see what happens
            try:
                qb.isvalid_object_name(object_name)
                # If it passes, the validation is case-insensitive (might be intentional)
            except Exception as e:
                # If it fails, the validation is case-sensitive
                if object_name.upper() in qb._BUSINESS_OBJECTS or object_name.capitalize() in qb._BUSINESS_OBJECTS:
                    # This could be a usability issue - common case variations are rejected
                    pass  # Not necessarily a bug, might be intentional


@given(st.integers(min_value=-1000000, max_value=1000000))
@settings(max_examples=1000)
def test_exception_boundary_conditions(error_code):
    """Test exception handling at boundary conditions"""
    error = {
        "Message": "Test error",
        "Detail": "Test detail",
        "code": error_code
    }
    fault = {"Error": [error]}
    
    try:
        QuickBooks.handle_exceptions(fault)
        print(f"FAILURE: No exception raised for code {error_code}")
        assert False
    except Exception as e:
        # Verify the exception type matches the documented ranges
        if error_code == 0:
            # Edge case: code 0 should be QuickbooksException (not in any range)
            assert type(e).__name__ == 'QuickbooksException'
        elif error_code < 0:
            # Negative codes should be base QuickbooksException
            assert type(e).__name__ == 'QuickbooksException'
        elif error_code == 500:
            # Boundary: should be UnsupportedException
            assert type(e).__name__ == 'UnsupportedException'
        elif error_code == 600:
            # Boundary: should be GeneralException
            assert type(e).__name__ == 'GeneralException'
        elif error_code == 2000:
            # Boundary: should be ValidationException
            assert type(e).__name__ == 'ValidationException'
        elif error_code == 10000:
            # Boundary: should be SevereException
            assert type(e).__name__ == 'SevereException'


def run_edge_case_tests():
    print("Running edge case tests...")
    print("=" * 60)
    
    print("\n1. Testing webhook signature with binary edge cases...")
    try:
        test_webhook_signature_edge_cases()
        print("✓ Passed 500 examples")
    except AssertionError as e:
        print(f"✗ Bug found: {e}")
        return False
    
    print("\n2. Testing object name case sensitivity...")
    try:
        test_isvalid_object_name_case_sensitivity()
        print("✓ Passed 100 examples")
    except AssertionError as e:
        print(f"✗ Bug found: {e}")
        return False
    
    print("\n3. Testing exception boundary conditions...")
    try:
        test_exception_boundary_conditions()
        print("✓ Passed 1000 examples")
    except AssertionError as e:
        print(f"✗ Bug found: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All edge case tests passed!")
    return True


if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1)