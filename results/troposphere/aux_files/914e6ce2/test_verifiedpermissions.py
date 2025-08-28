import re
from hypothesis import given, strategies as st, assume, settings
import troposphere.verifiedpermissions as vp
import pytest


# Strategy for valid CloudFormation resource titles (ASCII alphanumeric only)
# CloudFormation only accepts ASCII alphanumeric characters [a-zA-Z0-9]
valid_title_strategy = st.text(alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"), min_size=1, max_size=255)

# Strategy for normal strings
string_strategy = st.text(min_size=1, max_size=1000)

# Strategy for lists of strings  
string_list_strategy = st.lists(string_strategy, min_size=0, max_size=10)


class TestEntityIdentifier:
    """Test EntityIdentifier AWSProperty class"""
    
    @given(
        entity_id=string_strategy,
        entity_type=string_strategy
    )
    def test_round_trip_property(self, entity_id, entity_type):
        """Test that from_dict(to_dict(obj)) returns equivalent dict"""
        # Create object with properties
        original_obj = vp.EntityIdentifier(
            EntityId=entity_id,
            EntityType=entity_type
        )
        
        # Convert to dict
        dict_repr = original_obj.to_dict()
        
        # Create new object from dict
        new_obj = vp.EntityIdentifier._from_dict(**dict_repr)
        
        # Convert back to dict
        new_dict_repr = new_obj.to_dict()
        
        # They should be equal
        assert dict_repr == new_dict_repr
        
    def test_required_property_validation(self):
        """Test that missing required properties raise ValueError"""
        # EntityId is required
        obj = vp.EntityIdentifier(EntityType='test-type')
        with pytest.raises(ValueError, match="EntityId required"):
            obj.to_dict()
            
        # EntityType is required  
        obj = vp.EntityIdentifier(EntityId='test-id')
        with pytest.raises(ValueError, match="EntityType required"):
            obj.to_dict()
            
    @given(
        invalid_entity_id=st.one_of(st.integers(), st.lists(st.text()), st.dictionaries(st.text(), st.text())),
        valid_entity_type=string_strategy
    )
    def test_type_validation(self, invalid_entity_id, valid_entity_type):
        """Test that wrong types raise TypeError"""
        with pytest.raises(TypeError):
            vp.EntityIdentifier(EntityId=invalid_entity_id, EntityType=valid_entity_type)


class TestDeletionProtection:
    """Test DeletionProtection AWSProperty class"""
    
    @given(mode=string_strategy)
    def test_round_trip_property(self, mode):
        """Test that from_dict(to_dict(obj)) returns equivalent dict"""
        original_obj = vp.DeletionProtection(Mode=mode)
        dict_repr = original_obj.to_dict()
        new_obj = vp.DeletionProtection._from_dict(**dict_repr)
        new_dict_repr = new_obj.to_dict()
        assert dict_repr == new_dict_repr
        
    def test_required_property_validation(self):
        """Test that missing Mode raises ValueError"""
        obj = vp.DeletionProtection()
        with pytest.raises(ValueError, match="Mode required"):
            obj.to_dict()


class TestCognitoGroupConfiguration:
    """Test CognitoGroupConfiguration AWSProperty class"""
    
    @given(group_entity_type=string_strategy)
    def test_round_trip_property(self, group_entity_type):
        """Test that from_dict(to_dict(obj)) returns equivalent dict"""
        original_obj = vp.CognitoGroupConfiguration(GroupEntityType=group_entity_type)
        dict_repr = original_obj.to_dict()
        new_obj = vp.CognitoGroupConfiguration._from_dict(**dict_repr)
        new_dict_repr = new_obj.to_dict()
        assert dict_repr == new_dict_repr


class TestCognitoUserPoolConfiguration:
    """Test CognitoUserPoolConfiguration with nested objects"""
    
    @given(
        user_pool_arn=string_strategy,
        client_ids=st.one_of(st.none(), string_list_strategy),
        group_entity_type=st.one_of(st.none(), string_strategy)
    )
    def test_round_trip_with_nested_objects(self, user_pool_arn, client_ids, group_entity_type):
        """Test round-trip with optional nested CognitoGroupConfiguration"""
        kwargs = {'UserPoolArn': user_pool_arn}
        
        if client_ids is not None:
            kwargs['ClientIds'] = client_ids
            
        if group_entity_type is not None:
            kwargs['GroupConfiguration'] = vp.CognitoGroupConfiguration(
                GroupEntityType=group_entity_type
            )
        
        original_obj = vp.CognitoUserPoolConfiguration(**kwargs)
        dict_repr = original_obj.to_dict()
        new_obj = vp.CognitoUserPoolConfiguration._from_dict(**dict_repr)
        new_dict_repr = new_obj.to_dict()
        assert dict_repr == new_dict_repr


class TestPolicyStore:
    """Test PolicyStore AWSObject class"""
    
    @given(
        title=valid_title_strategy,
        mode=string_strategy,
        description=st.one_of(st.none(), string_strategy)
    )
    def test_round_trip_property(self, title, mode, description):
        """Test that from_dict(to_dict(obj)) returns equivalent dict for AWSObject"""
        kwargs = {
            'ValidationSettings': vp.ValidationSettings(Mode=mode)
        }
        
        if description is not None:
            kwargs['Description'] = description
            
        original_obj = vp.PolicyStore(title, **kwargs)
        
        # Note: to_dict() includes Type field for AWSObject
        dict_repr = original_obj.to_dict()
        
        # Extract properties for from_dict (excluding Type and title)
        properties = dict_repr.get('Properties', {})
        
        # Create new object from properties
        new_obj = vp.PolicyStore._from_dict(title, **properties)
        new_dict_repr = new_obj.to_dict()
        
        assert dict_repr == new_dict_repr
        
    @given(invalid_title=st.text(alphabet=st.characters(whitelist_categories=("P", "S")), min_size=1))
    def test_title_validation(self, invalid_title):
        """Test that non-alphanumeric titles raise ValueError"""
        # Ensure title has non-alphanumeric characters
        assume(not re.match(r'^[a-zA-Z0-9]+$', invalid_title))
        
        with pytest.raises(ValueError, match="not alphanumeric"):
            vp.PolicyStore(
                invalid_title,
                ValidationSettings=vp.ValidationSettings(Mode='STRICT')
            )


class TestPolicy:
    """Test Policy AWSObject class with complex nested PolicyDefinition"""
    
    @given(
        title=valid_title_strategy,
        policy_store_id=string_strategy,
        use_static=st.booleans(),
        statement=string_strategy,
        description=st.one_of(st.none(), string_strategy),
        template_id=string_strategy,
        entity_id=string_strategy,
        entity_type=string_strategy
    )
    def test_policy_definition_round_trip(
        self, title, policy_store_id, use_static, 
        statement, description, template_id, entity_id, entity_type
    ):
        """Test Policy with either Static or TemplateLinked PolicyDefinition"""
        
        if use_static:
            # Test with StaticPolicyDefinition
            static_kwargs = {'Statement': statement}
            if description is not None:
                static_kwargs['Description'] = description
                
            definition = vp.PolicyDefinition(
                Static=vp.StaticPolicyDefinition(**static_kwargs)
            )
        else:
            # Test with TemplateLinkedPolicyDefinition
            definition = vp.PolicyDefinition(
                TemplateLinked=vp.TemplateLinkedPolicyDefinition(
                    PolicyTemplateId=template_id,
                    Principal=vp.EntityIdentifier(
                        EntityId=entity_id,
                        EntityType=entity_type
                    )
                )
            )
        
        original_obj = vp.Policy(
            title,
            Definition=definition,
            PolicyStoreId=policy_store_id
        )
        
        dict_repr = original_obj.to_dict()
        properties = dict_repr.get('Properties', {})
        
        new_obj = vp.Policy._from_dict(title, **properties)
        new_dict_repr = new_obj.to_dict()
        
        assert dict_repr == new_dict_repr


class TestIdentitySource:
    """Test IdentitySource with complex nested configurations"""
    
    @given(
        title=valid_title_strategy,
        policy_store_id=string_strategy,
        use_cognito=st.booleans(),
        user_pool_arn=string_strategy,
        issuer=string_strategy,
        entity_prefix=st.one_of(st.none(), string_strategy),
        principal_id_claim=st.one_of(st.none(), string_strategy),
        audiences=st.one_of(st.none(), string_list_strategy)
    )
    @settings(max_examples=50)  # Reduce examples for complex nested structures
    def test_identity_source_configurations(
        self, title, policy_store_id, use_cognito,
        user_pool_arn, issuer, entity_prefix, 
        principal_id_claim, audiences
    ):
        """Test IdentitySource with either Cognito or OpenIdConnect configuration"""
        
        if use_cognito:
            # Test with CognitoUserPoolConfiguration
            config = vp.IdentitySourceConfiguration(
                CognitoUserPoolConfiguration=vp.CognitoUserPoolConfiguration(
                    UserPoolArn=user_pool_arn
                )
            )
        else:
            # Test with OpenIdConnectConfiguration
            access_token_config = vp.OpenIdConnectAccessTokenConfiguration()
            if audiences is not None:
                access_token_config = vp.OpenIdConnectAccessTokenConfiguration(
                    Audiences=audiences
                )
            if principal_id_claim is not None:
                access_token_config = vp.OpenIdConnectAccessTokenConfiguration(
                    PrincipalIdClaim=principal_id_claim
                )
                
            oidc_kwargs = {
                'Issuer': issuer,
                'TokenSelection': vp.OpenIdConnectTokenSelection(
                    AccessTokenOnly=access_token_config
                )
            }
            
            if entity_prefix is not None:
                oidc_kwargs['EntityIdPrefix'] = entity_prefix
                
            config = vp.IdentitySourceConfiguration(
                OpenIdConnectConfiguration=vp.OpenIdConnectConfiguration(**oidc_kwargs)
            )
        
        original_obj = vp.IdentitySource(
            title,
            Configuration=config,
            PolicyStoreId=policy_store_id
        )
        
        dict_repr = original_obj.to_dict()
        properties = dict_repr.get('Properties', {})
        
        new_obj = vp.IdentitySource._from_dict(title, **properties)
        new_dict_repr = new_obj.to_dict()
        
        assert dict_repr == new_dict_repr


class TestValidationSettings:
    """Test ValidationSettings edge cases"""
    
    @given(mode=string_strategy)
    def test_validation_settings_round_trip(self, mode):
        """Test simple round-trip for ValidationSettings"""
        obj = vp.ValidationSettings(Mode=mode)
        dict_repr = obj.to_dict()
        new_obj = vp.ValidationSettings._from_dict(**dict_repr)
        assert dict_repr == new_obj.to_dict()
        
    @given(invalid_mode=st.one_of(st.integers(), st.lists(st.text())))
    def test_validation_settings_type_checking(self, invalid_mode):
        """Test that ValidationSettings rejects non-string Mode"""
        with pytest.raises(TypeError):
            vp.ValidationSettings(Mode=invalid_mode)