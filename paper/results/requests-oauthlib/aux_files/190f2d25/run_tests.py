#!/usr/bin/env python3
"""Run property-based tests to find bugs in OAuth2Session."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import WebApplicationClient
import string
import traceback

# Test 1: PKCE validation
print("Testing PKCE validation property...")
try:
    @given(st.text(min_size=1).filter(lambda x: x not in ["S256", "plain"]))
    @settings(max_examples=100)
    def test_pkce_invalid(invalid_pkce):
        try:
            OAuth2Session(client_id="test", pkce=invalid_pkce)
            print(f"BUG: Invalid PKCE value '{invalid_pkce}' was accepted!")
            return False
        except AttributeError as e:
            if "Wrong value for" in str(e) and f"pkce={invalid_pkce}" in str(e):
                return True
            else:
                print(f"BUG: Wrong error message for invalid PKCE: {e}")
                return False
    
    test_pkce_invalid()
    print("✓ PKCE validation test passed")
except Exception as e:
    print(f"✗ PKCE validation test failed: {e}")
    traceback.print_exc()

# Test 2: Token property synchronization
print("\nTesting token property synchronization...")
try:
    @given(st.dictionaries(
        st.sampled_from(['access_token', 'token_type', 'refresh_token']),
        st.text(min_size=1),
        min_size=0,
        max_size=3
    ))
    @settings(max_examples=100)
    def test_token_sync(token):
        session = OAuth2Session(client_id="test")
        session.token = token
        
        if session.token != token:
            print(f"BUG: Token not synchronized properly. Set: {token}, Got: {session.token}")
            return False
        if session._client.token != token:
            print(f"BUG: Client token not synchronized. Set: {token}, Got: {session._client.token}")
            return False
        return True
    
    test_token_sync()
    print("✓ Token synchronization test passed")
except Exception as e:
    print(f"✗ Token synchronization test failed: {e}")
    traceback.print_exc()

# Test 3: Scope property fallback
print("\nTesting scope property fallback behavior...")
try:
    @given(
        st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5)),
        st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
    )
    @settings(max_examples=100)
    def test_scope_fallback(session_scope, client_scope):
        client = WebApplicationClient("test_id")
        client.scope = client_scope
        session = OAuth2Session(client=client, scope=session_scope)
        
        expected = session_scope if session_scope is not None else client_scope
        if session.scope != expected:
            print(f"BUG: Scope fallback failed. Session scope: {session_scope}, Client scope: {client_scope}, Got: {session.scope}, Expected: {expected}")
            return False
        return True
    
    test_scope_fallback()
    print("✓ Scope fallback test passed")
except Exception as e:
    print(f"✗ Scope fallback test failed: {e}")
    traceback.print_exc()

# Test 4: Compliance hook registration
print("\nTesting compliance hook registration...")
try:
    valid_hooks = ["access_token_response", "refresh_token_response", "protected_request", 
                   "refresh_token_request", "access_token_request"]
    
    @given(st.text(min_size=1).filter(lambda x: x not in valid_hooks))
    @settings(max_examples=100)
    def test_invalid_hook(invalid_hook_type):
        session = OAuth2Session()
        
        def dummy():
            pass
        
        try:
            session.register_compliance_hook(invalid_hook_type, dummy)
            print(f"BUG: Invalid hook type '{invalid_hook_type}' was accepted!")
            return False
        except ValueError as e:
            if "Hook type" in str(e):
                return True
            else:
                print(f"BUG: Wrong error for invalid hook: {e}")
                return False
    
    test_invalid_hook()
    print("✓ Invalid hook rejection test passed")
except Exception as e:
    print(f"✗ Invalid hook rejection test failed: {e}")
    traceback.print_exc()

# Test 5: Hook uniqueness (sets)
print("\nTesting compliance hook uniqueness...")
try:
    @given(st.sampled_from(["access_token_response", "refresh_token_response", "protected_request", 
                             "refresh_token_request", "access_token_request"]))
    @settings(max_examples=20)
    def test_hook_uniqueness(hook_type):
        session = OAuth2Session()
        
        def dummy():
            pass
        
        # Register same hook 3 times
        session.register_compliance_hook(hook_type, dummy)
        session.register_compliance_hook(hook_type, dummy)
        session.register_compliance_hook(hook_type, dummy)
        
        # Should only be stored once
        if len(session.compliance_hook[hook_type]) != 1:
            print(f"BUG: Hook not stored uniquely. Count: {len(session.compliance_hook[hook_type])}")
            return False
        if dummy not in session.compliance_hook[hook_type]:
            print(f"BUG: Hook not found in set")
            return False
        return True
    
    test_hook_uniqueness()
    print("✓ Hook uniqueness test passed")
except Exception as e:
    print(f"✗ Hook uniqueness test failed: {e}")
    traceback.print_exc()

# Test 6: Client ID round-trip
print("\nTesting client_id property round-trip...")
try:
    @given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits))
    @settings(max_examples=100)
    def test_client_id_roundtrip(client_id):
        session = OAuth2Session(client_id=client_id)
        
        # Test getter
        if session.client_id != client_id:
            print(f"BUG: client_id getter failed. Expected: {client_id}, Got: {session.client_id}")
            return False
        
        # Test setter
        new_id = client_id + "_mod"
        session.client_id = new_id
        if session.client_id != new_id:
            print(f"BUG: client_id setter failed. Set: {new_id}, Got: {session.client_id}")
            return False
        
        # Test deleter
        del session.client_id
        if session.client_id is not None:
            print(f"BUG: client_id deleter failed. Expected None, Got: {session.client_id}")
            return False
        
        return True
    
    test_client_id_roundtrip()
    print("✓ Client ID round-trip test passed")
except Exception as e:
    print(f"✗ Client ID round-trip test failed: {e}")
    traceback.print_exc()

# Test 7: Access token property
print("\nTesting access_token property...")
try:
    @given(st.text(min_size=1))
    @settings(max_examples=100)
    def test_access_token(token):
        session = OAuth2Session(client_id="test")
        
        # Set via property
        session.access_token = token
        
        # Check getter
        if session.access_token != token:
            print(f"BUG: access_token getter failed. Set: {token}, Got: {session.access_token}")
            return False
        
        # Check it's on client too
        if session._client.access_token != token:
            print(f"BUG: access_token not synced to client. Expected: {token}, Got: {session._client.access_token}")
            return False
        
        # Test deleter
        del session.access_token
        if session.access_token is not None:
            print(f"BUG: access_token deleter failed. Expected None, Got: {session.access_token}")
            return False
        
        return True
    
    test_access_token()
    print("✓ Access token property test passed")
except Exception as e:
    print(f"✗ Access token property test failed: {e}")
    traceback.print_exc()

# Test 8: Authorized property
print("\nTesting authorized property...")
try:
    session = OAuth2Session()
    
    # No token - should be False
    if session.authorized:
        print(f"BUG: authorized should be False with no token")
    
    # With token - should be True
    session.access_token = "test_token"
    if not session.authorized:
        print(f"BUG: authorized should be True with token")
    
    # Remove token - should be False again
    del session.access_token
    if session.authorized:
        print(f"BUG: authorized should be False after deleting token")
    
    print("✓ Authorized property test passed")
except Exception as e:
    print(f"✗ Authorized property test failed: {e}")
    traceback.print_exc()

print("\n=== All tests completed ===")