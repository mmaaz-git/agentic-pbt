#!/usr/bin/env python3
"""Test for real bugs in OAuth2Session using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import WebApplicationClient
import traceback

print("=== Testing for Real Bugs in OAuth2Session ===\n")

# Bug Hunt 1: Testing scope property setter/getter consistency
print("Test 1: Scope property setter behavior...")

@composite
def scope_values(draw):
    """Generate various scope values including edge cases."""
    return draw(st.one_of(
        st.none(),
        st.just([]),  # Empty list
        st.just(""),  # Empty string (should this be valid?)
        st.just("single_scope"),  # String instead of list
        st.lists(st.text(min_size=1), min_size=1, max_size=3),
        st.just(["scope1", "scope2", "scope3"])
    ))

@given(scope_values())
@settings(max_examples=50)
def test_scope_setter(scope_value):
    """Test if scope setter properly handles various input types."""
    session = OAuth2Session(client_id="test")
    
    try:
        # Set the scope
        session.scope = scope_value
        
        # Get it back
        retrieved = session.scope
        
        # Check consistency
        if session._scope != scope_value:
            print(f"BUG: Scope setter inconsistency!")
            print(f"  Set: {repr(scope_value)}")
            print(f"  Internal _scope: {repr(session._scope)}")
            print(f"  Retrieved via property: {repr(retrieved)}")
            return False
            
        # The setter should accept any value, even invalid ones
        # This might be a design issue if strings are accepted when lists are expected
        
    except Exception as e:
        print(f"Unexpected error with scope {repr(scope_value)}: {e}")
        return False
    
    return True

try:
    test_scope_setter()
    print("✓ Scope setter test completed\n")
except Exception as e:
    print(f"✗ Scope setter test failed: {e}\n")

# Bug Hunt 2: Testing token property with edge cases
print("Test 2: Token property with non-dict values...")

@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
@settings(max_examples=50)
def test_token_property_types(token_value):
    """Test token property with various types."""
    session = OAuth2Session(client_id="test")
    
    try:
        # Token setter calls _client.populate_token_attributes(value)
        # What happens if value is not a dict?
        session.token = token_value
        
        # This might fail if token_value is not a dict
        # Let's see if there's proper validation
        
    except (TypeError, AttributeError) as e:
        # Expected for non-dict values
        if not isinstance(token_value, (dict, type(None))):
            return True  # Correctly rejected
        else:
            print(f"BUG: Dict/None token rejected: {repr(token_value)}")
            print(f"  Error: {e}")
            return False
    except Exception as e:
        print(f"Unexpected error with token {type(token_value)}: {e}")
        return False
    
    # If we got here, the token was accepted
    if not isinstance(token_value, (dict, type(None))):
        print(f"BUG: Non-dict token accepted: {type(token_value)} = {repr(token_value)}")
        return False
    
    return True

try:
    test_token_property_types()
    print("✓ Token type test completed\n")
except Exception as e:
    print(f"✗ Token type test failed: {e}\n")

# Bug Hunt 3: State generation edge cases
print("Test 3: State generation with callable that raises exception...")

def bad_state_generator():
    """A state generator that raises an exception."""
    raise ValueError("Intentional error in state generator")

try:
    session = OAuth2Session(client_id="test", state=bad_state_generator)
    state = session.new_state()
    print(f"BUG: Exception in state generator not handled properly!")
    print(f"  Generated state: {repr(state)}")
except TypeError:
    # Expected - the exception is caught and treated as non-callable
    print("✓ State generator exception handled correctly")
except ValueError as e:
    if "Intentional error" in str(e):
        print("Potential BUG: State generator exception propagated directly")
        print("  This could crash user applications unexpectedly")
    else:
        print(f"Unexpected error: {e}")
except Exception as e:
    print(f"Unexpected error type: {type(e).__name__}: {e}")

print()

# Bug Hunt 4: Testing compliance hook registration with None
print("Test 4: Registering None as a compliance hook...")

session = OAuth2Session(client_id="test")
try:
    # What happens if we register None as a hook?
    session.register_compliance_hook("protected_request", None)
    
    # Now try to use it
    if None in session.compliance_hook["protected_request"]:
        print("BUG: None accepted as a valid hook function!")
        print("  This will cause TypeError when the hook is invoked")
        
        # This is a real bug - the hooks are called in various places like:
        # for hook in self.compliance_hook["protected_request"]:
        #     url, headers, data = hook(url, headers, data)
        # If hook is None, this will raise TypeError: 'NoneType' object is not callable
except Exception as e:
    print(f"Good: None rejected as hook: {e}")

print()

# Bug Hunt 5: Testing client_id with non-string values
print("Test 5: Setting client_id to non-string values...")

@given(st.one_of(
    st.integers(),
    st.floats(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text()),
    st.just(None),
    st.just(False),
    st.just(True)
))
@settings(max_examples=30)
def test_client_id_types(client_id_value):
    """Test client_id with various non-string types."""
    try:
        # First test in constructor
        session = OAuth2Session(client_id=client_id_value)
        
        # The client_id is passed to WebApplicationClient
        # which might or might not validate it
        
        # Also test setter
        session.client_id = client_id_value
        
        # No validation seems to happen - any type is accepted
        # This could cause issues later when the client_id is used
        
    except Exception as e:
        print(f"Error with client_id type {type(client_id_value)}: {e}")
        return False
    
    return True

try:
    test_client_id_types()
    print("✓ Client ID type test completed")
    print("  Note: client_id accepts any type - this might cause issues later\n")
except Exception as e:
    print(f"✗ Client ID type test failed: {e}\n")

# Bug Hunt 6: Testing authorization_url with insecure URL
print("Test 6: Authorization URL with HTTP (insecure)...")

session = OAuth2Session(client_id="test")
try:
    # The authorization_url method doesn't seem to check for HTTPS
    # Let's test with HTTP
    url, state = session.authorization_url("http://example.com/authorize")
    print("Potential BUG: HTTP URL accepted for authorization!")
    print(f"  Generated URL: {url[:50]}...")
    print("  OAuth 2.0 requires HTTPS for authorization endpoints")
except Exception as e:
    print(f"Good: Insecure URL rejected: {e}")

print()

# Bug Hunt 7: Empty string as state
print("Test 7: Using empty string as state...")

session = OAuth2Session(client_id="test", state="")
try:
    # Empty string as state is a security issue - it provides no CSRF protection
    url, state = session.authorization_url("https://example.com/authorize")
    if state == "":
        print("BUG: Empty string accepted as state value!")
        print("  This provides no CSRF protection")
        print(f"  Generated URL: {url[:80]}...")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Testing Complete ===")