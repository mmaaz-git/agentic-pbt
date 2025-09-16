#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

import math
import hashlib
import hmac
import base64
from hypothesis import given, strategies as st, assume, settings
from quickbooks import utils, exceptions
from quickbooks.client import QuickBooks, to_bytes
import traceback


def test_single_quote_escaping():
    """Test specific case where SQL injection might occur"""
    # Test with a string containing single quote
    test_value = "O'Reilly"
    params = {"name": test_value}
    where_clause = utils.build_where_clause(**params)
    print(f"Test 1: Input: {test_value}")
    print(f"Output: {where_clause}")
    
    # Check if the quote is escaped
    if r"\'" in where_clause:
        print("✓ Single quote properly escaped")
    else:
        print("✗ VULNERABILITY: Single quote not escaped!")
        return False
    
    # Test with SQL injection attempt
    injection_attempt = "'; DROP TABLE users; --"
    params = {"name": injection_attempt}
    where_clause = utils.build_where_clause(**params)
    print(f"\nTest 2: Input: {injection_attempt}")
    print(f"Output: {where_clause}")
    
    if "DROP TABLE" in where_clause and r"\'" not in where_clause:
        print("✗ VULNERABILITY: SQL injection not prevented!")
        return False
    else:
        print("✓ SQL injection attempt escaped")
    
    return True


def test_choose_clause_escaping():
    """Test escaping in build_choose_clause"""
    choices = ["O'Reilly", "Smith", "'; DROP TABLE users; --"]
    field = "name"
    where_clause = utils.build_choose_clause(choices, field)
    print(f"\nTest 3: Choices: {choices}")
    print(f"Output: {where_clause}")
    
    # Check each choice is properly escaped
    for choice in choices:
        if "'" in choice:
            escaped = choice.replace("'", r"\'")
            if escaped in where_clause:
                print(f"✓ '{choice}' properly escaped")
            else:
                print(f"✗ VULNERABILITY: '{choice}' not escaped!")
                return False
    
    return True


def test_exception_mapping():
    """Test exception code range mapping"""
    test_cases = [
        (100, exceptions.AuthorizationException),
        (550, exceptions.UnsupportedException),
        (610, exceptions.ObjectNotFoundException),
        (1500, exceptions.GeneralException),
        (3000, exceptions.ValidationException),
        (15000, exceptions.SevereException),
        (-100, exceptions.QuickbooksException),
        (0, exceptions.QuickbooksException),
    ]
    
    print("\nTest 4: Exception code mapping")
    
    for code, expected_exception in test_cases:
        error = {
            "Message": "Test error",
            "Detail": "Test detail",
            "code": code
        }
        fault = {"Error": [error]}
        
        try:
            QuickBooks.handle_exceptions(fault)
            print(f"✗ Code {code}: No exception raised!")
            return False
        except Exception as e:
            if isinstance(e, expected_exception):
                print(f"✓ Code {code}: Correct exception type {expected_exception.__name__}")
            else:
                print(f"✗ Code {code}: Expected {expected_exception.__name__}, got {type(e).__name__}")
                return False
    
    return True


def test_webhook_signature():
    """Test webhook signature validation"""
    print("\nTest 5: Webhook signature validation")
    
    request_body = b"test body content"
    verifier_token = "secret_token"
    
    # Generate valid signature
    hmac_hash = hmac.new(
        to_bytes(verifier_token),
        request_body,
        hashlib.sha256
    ).digest()
    valid_signature = base64.b64encode(hmac_hash).decode('utf-8')
    
    qb = QuickBooks()
    qb.verifier_token = verifier_token
    
    # Test valid signature
    request_body_str = request_body.decode('utf-8')
    result = qb.validate_webhook_signature(request_body_str, valid_signature)
    if result:
        print("✓ Valid signature accepted")
    else:
        print("✗ Valid signature rejected!")
        return False
    
    # Test invalid signature
    invalid_signature = base64.b64encode(b"invalid").decode('utf-8')
    result = qb.validate_webhook_signature(request_body_str, invalid_signature)
    if not result:
        print("✓ Invalid signature rejected")
    else:
        print("✗ Invalid signature accepted!")
        return False
    
    return True


def main():
    print("Running QuickBooks property tests...\n")
    print("=" * 60)
    
    all_passed = True
    
    try:
        if not test_single_quote_escaping():
            all_passed = False
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        traceback.print_exc()
        all_passed = False
    
    try:
        if not test_choose_clause_escaping():
            all_passed = False
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        traceback.print_exc()
        all_passed = False
    
    try:
        if not test_exception_mapping():
            all_passed = False
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        traceback.print_exc()
        all_passed = False
    
    try:
        if not test_webhook_signature():
            all_passed = False
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed - check output above")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)