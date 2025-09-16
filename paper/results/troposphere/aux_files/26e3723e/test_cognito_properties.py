#!/usr/bin/env python3
"""Property-based tests for troposphere.cognito module."""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings, example
import pytest
from troposphere import cognito
from troposphere.validators.cognito import validate_recoveryoption_name


# Strategy for valid alphanumeric titles
def valid_title_strategy():
    return st.text(
        alphabet=st.characters(whitelist_categories=(), whitelist_characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
        min_size=1,
        max_size=50
    )


# Strategy for invalid titles (containing non-alphanumeric)
def invalid_title_strategy():
    # Generate text that contains at least one non-alphanumeric character
    return st.text(min_size=1, max_size=50).filter(
        lambda s: not re.match(r'^[a-zA-Z0-9]+$', s) and s != ""
    )


class TestTitleValidation:
    """Test the title validation property that titles must be alphanumeric."""
    
    @given(title=valid_title_strategy())
    def test_valid_titles_accepted(self, title):
        """Valid alphanumeric titles should be accepted."""
        pool = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=True
        )
        assert pool.title == title
    
    @given(title=invalid_title_strategy())
    @example(title="test-pool")  # dash is invalid
    @example(title="test pool")  # space is invalid  
    @example(title="test_pool")  # underscore is invalid
    @example(title="")          # empty is invalid
    def test_invalid_titles_rejected(self, title):
        """Non-alphanumeric titles should raise ValueError."""
        with pytest.raises(ValueError, match="not alphanumeric"):
            cognito.IdentityPool(
                title=title,
                AllowUnauthenticatedIdentities=True
            )


class TestRequiredProperties:
    """Test required property validation."""
    
    @given(title=valid_title_strategy())
    def test_identity_pool_requires_allow_unauth(self, title):
        """IdentityPool without AllowUnauthenticatedIdentities should fail validation."""
        pool = cognito.IdentityPool(title=title)
        with pytest.raises(ValueError, match="AllowUnauthenticatedIdentities required"):
            pool.to_dict()
    
    @given(title=valid_title_strategy(), pool_id=st.text(min_size=1, max_size=50))
    def test_log_delivery_requires_user_pool_id(self, title, pool_id):
        """LogDeliveryConfiguration without UserPoolId should fail validation."""
        config = cognito.LogDeliveryConfiguration(title=title)
        with pytest.raises(ValueError, match="UserPoolId required"):
            config.to_dict()
    
    @given(title=valid_title_strategy(), pool_id=st.text(min_size=1, max_size=50))
    def test_user_pool_client_requires_user_pool_id(self, title, pool_id):
        """UserPoolClient without UserPoolId should fail validation."""
        client = cognito.UserPoolClient(title=title)
        with pytest.raises(ValueError, match="UserPoolId required"):
            client.to_dict()


class TestRecoveryOptionValidation:
    """Test the RecoveryOption name validation."""
    
    @given(name=st.sampled_from(["admin_only", "verified_email", "verified_phone_number"]))
    def test_valid_recovery_option_names(self, name):
        """Valid recovery option names should be accepted."""
        result = validate_recoveryoption_name(name)
        assert result == name
    
    @given(name=st.text().filter(lambda x: x not in ["admin_only", "verified_email", "verified_phone_number"]))
    @example(name="email")
    @example(name="phone")
    @example(name="admin")
    @example(name="ADMIN_ONLY")
    def test_invalid_recovery_option_names(self, name):
        """Invalid recovery option names should raise ValueError."""
        with pytest.raises(ValueError, match="RecoveryOption Name must be one of"):
            validate_recoveryoption_name(name)


class TestSerializationRoundTrip:
    """Test serialization round-trip properties."""
    
    @given(
        title=valid_title_strategy(),
        allow_unauth=st.booleans(),
        allow_classic=st.booleans()
    )
    def test_identity_pool_dict_round_trip(self, title, allow_unauth, allow_classic):
        """IdentityPool should survive to_dict/from_dict round trip."""
        pool1 = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=allow_unauth,
            AllowClassicFlow=allow_classic
        )
        
        dict_repr = pool1.to_dict()
        pool2 = cognito.IdentityPool.from_dict(
            title=title,
            d=dict_repr["Properties"]
        )
        
        # Compare the dict representations
        assert pool1.to_dict() == pool2.to_dict()
    
    @given(
        title=valid_title_strategy(),
        user_pool_id=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
        log_level=st.sampled_from(["ERROR", "INFO", "DEBUG"])
    )
    def test_log_delivery_config_round_trip(self, title, user_pool_id, log_level):
        """LogDeliveryConfiguration should survive to_dict/from_dict round trip."""
        config1 = cognito.LogDeliveryConfiguration(
            title=title,
            UserPoolId=user_pool_id,
            LogConfigurations=[
                cognito.LogConfiguration(
                    LogLevel=log_level,
                    EventSource="UserAuthentication"
                )
            ]
        )
        
        dict_repr = config1.to_dict()
        config2 = cognito.LogDeliveryConfiguration.from_dict(
            title=title,
            d=dict_repr["Properties"]
        )
        
        assert config1.to_dict() == config2.to_dict()


class TestEqualityProperties:
    """Test object equality properties."""
    
    @given(
        title=valid_title_strategy(),
        allow_unauth=st.booleans()
    )
    def test_equal_pools_are_equal(self, title, allow_unauth):
        """Two IdentityPools with same properties should be equal."""
        pool1 = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=allow_unauth
        )
        pool2 = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=allow_unauth
        )
        
        assert pool1 == pool2
        assert hash(pool1) == hash(pool2)
    
    @given(
        title1=valid_title_strategy(),
        title2=valid_title_strategy(),
        allow_unauth=st.booleans()
    )
    def test_different_titles_make_unequal(self, title1, title2, allow_unauth):
        """IdentityPools with different titles should not be equal."""
        assume(title1 != title2)
        
        pool1 = cognito.IdentityPool(
            title=title1,
            AllowUnauthenticatedIdentities=allow_unauth
        )
        pool2 = cognito.IdentityPool(
            title=title2,
            AllowUnauthenticatedIdentities=allow_unauth
        )
        
        assert pool1 != pool2
    
    @given(
        title=valid_title_strategy(),
        allow_unauth1=st.booleans(),
        allow_unauth2=st.booleans()
    )
    def test_different_properties_make_unequal(self, title, allow_unauth1, allow_unauth2):
        """IdentityPools with different properties should not be equal."""
        assume(allow_unauth1 != allow_unauth2)
        
        pool1 = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=allow_unauth1
        )
        pool2 = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=allow_unauth2
        )
        
        assert pool1 != pool2


class TestTypeValidation:
    """Test property type validation."""
    
    @given(
        title=valid_title_strategy(),
        value=st.one_of(
            st.booleans(),
            st.text(alphabet="01", min_size=1, max_size=1).map(lambda x: x == "1"),
            st.sampled_from([0, 1]),
            st.sampled_from(["true", "false", "True", "False"])
        )
    )
    def test_boolean_property_accepts_various_types(self, title, value):
        """Boolean properties should accept booleans and convertible values."""
        pool = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=value
        )
        # Should not raise during creation
        assert pool is not None
        # to_dict should handle the conversion
        result = pool.to_dict()
        assert result is not None
    
    @given(
        title=valid_title_strategy(),
        server_check=st.one_of(
            st.booleans(),
            st.text(alphabet="01", min_size=1, max_size=1).map(lambda x: x == "1"),
            st.sampled_from([0, 1]),
            st.sampled_from(["true", "false", "True", "False"])
        )
    )
    def test_cognito_provider_boolean_field(self, title, server_check):
        """CognitoIdentityProvider boolean field should accept various types."""
        provider = cognito.CognitoIdentityProvider(
            ClientId="test-client",
            ProviderName="test-provider",
            ServerSideTokenCheck=server_check
        )
        # Should not raise
        assert provider is not None
    
    @given(
        title=valid_title_strategy(),
        arns=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5)
    )
    def test_list_properties_accept_lists(self, title, arns):
        """List properties should accept lists."""
        pool = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=True,
            OpenIdConnectProviderARNs=arns
        )
        dict_repr = pool.to_dict()
        if arns:
            assert dict_repr["Properties"]["OpenIdConnectProviderARNs"] == arns


class TestDictProperties:
    """Test dictionary properties."""
    
    @given(
        title=valid_title_strategy(),
        providers=st.dictionaries(
            st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20),
            st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5
        )
    )
    def test_supported_login_providers_accepts_dict(self, title, providers):
        """SupportedLoginProviders should accept dictionaries."""
        pool = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=True,
            SupportedLoginProviders=providers
        )
        dict_repr = pool.to_dict()
        if providers:
            assert dict_repr["Properties"]["SupportedLoginProviders"] == providers
    
    @given(
        title=valid_title_strategy(),
        events=st.dictionaries(
            st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20),
            st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5
        )
    )
    def test_cognito_events_accepts_dict(self, title, events):
        """CognitoEvents should accept dictionaries."""
        pool = cognito.IdentityPool(
            title=title,
            AllowUnauthenticatedIdentities=True,
            CognitoEvents=events
        )
        dict_repr = pool.to_dict()
        if events:
            assert dict_repr["Properties"]["CognitoEvents"] == events