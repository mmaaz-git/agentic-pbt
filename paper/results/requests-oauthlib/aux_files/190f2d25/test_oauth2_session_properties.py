#!/usr/bin/env python3
"""Property-based tests for requests_oauthlib.oauth2_session using Hypothesis."""

import sys
import os

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import pytest
from requests_oauthlib import OAuth2Session, TokenUpdated
from oauthlib.oauth2 import WebApplicationClient, LegacyApplicationClient
import string
import requests

# Strategy for valid client IDs (non-empty strings)
client_id_strategy = st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "-_")

# Strategy for valid PKCE values  
pkce_strategy = st.sampled_from(["S256", "plain", None])

# Strategy for invalid PKCE values (anything other than the valid ones)
invalid_pkce_strategy = st.text(min_size=1).filter(lambda x: x not in ["S256", "plain"])

# Strategy for token dictionaries
@composite
def token_dict_strategy(draw):
    """Generate valid token dictionaries."""
    token = {}
    if draw(st.booleans()):
        token['access_token'] = draw(st.text(min_size=1))
    if draw(st.booleans()):
        token['token_type'] = draw(st.sampled_from(['Bearer', 'MAC', 'JWT']))
    if draw(st.booleans()):
        token['refresh_token'] = draw(st.text(min_size=1))
    if draw(st.booleans()):
        token['expires_in'] = draw(st.integers(min_value=0, max_value=3600000))
    return token

# Strategy for scope values
scope_strategy = st.one_of(
    st.none(),
    st.lists(st.text(min_size=1, max_size=20, alphabet=string.ascii_letters), min_size=1, max_size=10)
)

# Strategy for compliance hook types
valid_hook_types = ["access_token_response", "refresh_token_response", "protected_request", 
                    "refresh_token_request", "access_token_request"]
hook_type_strategy = st.sampled_from(valid_hook_types)
invalid_hook_type_strategy = st.text(min_size=1).filter(lambda x: x not in valid_hook_types)


class TestOAuth2SessionProperties:
    """Test properties of OAuth2Session class."""
    
    @given(invalid_pkce_strategy, client_id_strategy)
    def test_pkce_validation_rejects_invalid_values(self, invalid_pkce, client_id):
        """Test that invalid PKCE values raise AttributeError as per line 89-90."""
        with pytest.raises(AttributeError) as exc_info:
            OAuth2Session(client_id=client_id, pkce=invalid_pkce)
        assert "Wrong value for" in str(exc_info.value)
        assert f"pkce={invalid_pkce}" in str(exc_info.value)
    
    @given(pkce_strategy, client_id_strategy)
    def test_pkce_validation_accepts_valid_values(self, valid_pkce, client_id):
        """Test that valid PKCE values are accepted (S256, plain, None)."""
        # Should not raise any exception
        session = OAuth2Session(client_id=client_id, pkce=valid_pkce)
        assert session._pkce == valid_pkce
    
    @given(client_id_strategy, token_dict_strategy())
    def test_token_property_synchronization(self, client_id, token):
        """Test that token property setter properly synchronizes with client (lines 146-149)."""
        session = OAuth2Session(client_id=client_id)
        
        # Set the token
        session.token = token
        
        # Check that token was set on both session and client
        assert session.token == token
        assert session._client.token == token
    
    @given(client_id_strategy, st.text(min_size=1))
    def test_access_token_property_consistency(self, client_id, access_token):
        """Test that access_token property is consistent with token dict."""
        session = OAuth2Session(client_id=client_id)
        
        # Set access token via property
        session.access_token = access_token
        
        # Check it's accessible via property
        assert session.access_token == access_token
        assert session._client.access_token == access_token
        
        # Delete and check it's gone
        del session.access_token
        assert session.access_token is None
    
    @given(client_id_strategy, scope_strategy, scope_strategy)
    def test_scope_property_fallback(self, client_id, session_scope, client_scope):
        """Test scope property fallback behavior (lines 106-118)."""
        # Create a client with a scope
        client = WebApplicationClient(client_id)
        client.scope = client_scope
        
        # Create session with this client
        session = OAuth2Session(client=client, scope=session_scope)
        
        # If session scope is set, it should take precedence
        if session_scope is not None:
            assert session.scope == session_scope
        # Otherwise, it should fall back to client scope
        else:
            assert session.scope == client_scope
    
    @given(client_id_strategy)
    def test_client_id_property_round_trip(self, client_id):
        """Test client_id property getter/setter/deleter (lines 131-140)."""
        session = OAuth2Session(client_id=client_id)
        
        # Test getter
        assert session.client_id == client_id
        
        # Test setter
        new_id = client_id + "_modified"
        session.client_id = new_id
        assert session.client_id == new_id
        assert session._client.client_id == new_id
        
        # Test deleter
        del session.client_id
        assert session.client_id is None
    
    @given(hook_type_strategy)
    def test_register_valid_compliance_hook(self, hook_type):
        """Test that valid hook types can be registered (lines 583-587)."""
        session = OAuth2Session()
        
        def dummy_hook(*args, **kwargs):
            pass
        
        # Should not raise for valid hook types
        session.register_compliance_hook(hook_type, dummy_hook)
        
        # Check hook was added to the set
        assert dummy_hook in session.compliance_hook[hook_type]
    
    @given(invalid_hook_type_strategy)
    def test_register_invalid_compliance_hook_raises(self, invalid_hook_type):
        """Test that invalid hook types raise ValueError (lines 583-586)."""
        session = OAuth2Session()
        
        def dummy_hook(*args, **kwargs):
            pass
        
        with pytest.raises(ValueError) as exc_info:
            session.register_compliance_hook(invalid_hook_type, dummy_hook)
        
        assert "Hook type" in str(exc_info.value)
        assert invalid_hook_type in str(exc_info.value)
    
    @given(hook_type_strategy)
    def test_compliance_hook_uniqueness(self, hook_type):
        """Test that hooks are stored as sets and maintain uniqueness."""
        session = OAuth2Session()
        
        def dummy_hook(*args, **kwargs):
            pass
        
        # Register the same hook multiple times
        session.register_compliance_hook(hook_type, dummy_hook)
        session.register_compliance_hook(hook_type, dummy_hook)
        session.register_compliance_hook(hook_type, dummy_hook)
        
        # Should only be stored once (as it's a set)
        assert len(session.compliance_hook[hook_type]) == 1
        assert dummy_hook in session.compliance_hook[hook_type]
    
    @given(st.booleans())
    def test_authorized_property_reflects_access_token(self, has_token):
        """Test that authorized property correctly reflects access_token presence (lines 164-172)."""
        session = OAuth2Session()
        
        if has_token:
            session.access_token = "test_token"
            assert session.authorized is True
        else:
            # No token set
            assert session.authorized is False
    
    @given(client_id_strategy)
    def test_state_generator_consistency(self, client_id):
        """Test new_state() method behavior with callable vs non-callable state (lines 120-128)."""
        # Test with callable state
        def state_generator():
            return "generated_state"
        
        session1 = OAuth2Session(client_id=client_id, state=state_generator)
        state1 = session1.new_state()
        assert state1 == "generated_state"
        assert session1._state == "generated_state"
        
        # Test with non-callable state (string)
        session2 = OAuth2Session(client_id=client_id, state="fixed_state")
        state2 = session2.new_state()
        assert state2 == "fixed_state"
        assert session2._state == "fixed_state"
    
    @given(client_id_strategy, st.text(min_size=1))
    def test_constructor_default_auth_lambda(self, client_id, test_value):
        """Test that default auth is set to identity lambda (line 94)."""
        session = OAuth2Session(client_id=client_id)
        
        # The auth should be a lambda that returns its input unchanged
        assert callable(session.auth)
        assert session.auth(test_value) == test_value
    
    @given(client_id_strategy)
    def test_compliance_hook_initialization(self, client_id):
        """Test that compliance hooks are initialized as empty sets (lines 98-104)."""
        session = OAuth2Session(client_id=client_id)
        
        expected_hooks = {
            "access_token_response", 
            "refresh_token_response",
            "protected_request",
            "refresh_token_request",
            "access_token_request"
        }
        
        # Check all hooks exist and are empty sets
        assert set(session.compliance_hook.keys()) == expected_hooks
        for hook_type in expected_hooks:
            assert isinstance(session.compliance_hook[hook_type], set)
            assert len(session.compliance_hook[hook_type]) == 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])