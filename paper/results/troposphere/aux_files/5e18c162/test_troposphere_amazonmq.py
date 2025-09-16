#!/usr/bin/env python3
"""
Property-based tests for troposphere.amazonmq module.
Testing fundamental properties that the code claims to have.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import pytest
import json
from troposphere.amazonmq import (
    Broker, Configuration, ConfigurationAssociation,
    ConfigurationId, EncryptionOptions, LdapServerMetadata,
    LogsConfiguration, MaintenanceWindow, User
)
from troposphere import Tags, Template
from troposphere.validators import boolean, integer
from troposphere.validators.amazonmq import validate_tags_or_list


# Strategy for valid alphanumeric titles
valid_title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=50
).filter(lambda x: x[0].isalpha())  # Must start with letter


# Strategy for booleans that should be accepted
boolean_inputs = st.sampled_from([
    True, False, 
    1, 0,
    "1", "0",
    "true", "false",
    "True", "False"
])


# Strategy for integer-like inputs
integer_inputs = st.one_of(
    st.integers(),
    st.text(min_size=1).map(lambda x: str(st.integers().example())),
)


class TestValidators:
    """Test the validators used by amazonmq module"""
    
    @given(boolean_inputs)
    def test_boolean_validator_accepts_valid_inputs(self, value):
        """Property: boolean validator accepts various true/false representations"""
        result = boolean(value)
        assert isinstance(result, bool)
        
        # Verify consistency: same input always produces same output
        assert boolean(value) == result
        
        # Verify correct mapping
        if value in [True, 1, "1", "true", "True"]:
            assert result is True
        elif value in [False, 0, "0", "false", "False"]:
            assert result is False
    
    @given(st.text().filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]))
    def test_boolean_validator_rejects_invalid_inputs(self, value):
        """Property: boolean validator rejects non-boolean representations"""
        assume(value not in [1, 0, True, False])  # These are valid
        with pytest.raises(ValueError):
            boolean(value)
    
    @given(st.integers())
    def test_integer_validator_accepts_integers(self, value):
        """Property: integer validator accepts all integers"""
        result = integer(value)
        assert result == value
        assert int(result) == value
    
    @given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: not x.is_integer()))
    def test_integer_validator_rejects_floats(self, value):
        """Property: integer validator rejects non-integer numbers"""
        with pytest.raises(ValueError, match="is not a valid integer"):
            integer(value)
    
    @given(st.one_of(
        st.lists(st.integers()),
        Tags(),
        st.builds(lambda: Tags({"Key1": "Value1"}))
    ))
    def test_tags_validator_accepts_valid_inputs(self, value):
        """Property: tags_or_list accepts Tags objects and lists"""
        result = validate_tags_or_list(value)
        assert result is value


class TestBrokerProperties:
    """Test properties of the Broker class"""
    
    @given(valid_title_strategy)
    def test_broker_title_validation(self, title):
        """Property: Broker accepts alphanumeric titles"""
        broker = Broker(
            title,
            BrokerName="TestBroker",
            DeploymentMode="SINGLE_INSTANCE",
            EngineType="ACTIVEMQ",
            HostInstanceType="mq.t3.micro",
            PubliclyAccessible=True,
            Users=[User(Username="admin", Password="password123")]
        )
        assert broker.title == title
    
    @given(st.text(min_size=1).filter(lambda x: not x.replace('_', '').replace('-', '').isalnum() or ' ' in x))
    def test_broker_invalid_title_rejected(self, title):
        """Property: Broker rejects non-alphanumeric titles"""
        assume(not title.isalnum())  # Ensure it's actually invalid
        with pytest.raises(ValueError, match="not alphanumeric"):
            Broker(
                title,
                BrokerName="TestBroker",
                DeploymentMode="SINGLE_INSTANCE", 
                EngineType="ACTIVEMQ",
                HostInstanceType="mq.t3.micro",
                PubliclyAccessible=True,
                Users=[User(Username="admin", Password="password123")]
            )
    
    @given(valid_title_strategy, st.text(min_size=1))
    def test_broker_required_properties(self, title, broker_name):
        """Property: Broker enforces required properties"""
        # Missing required properties should fail on to_dict()
        broker = Broker(title)
        broker.BrokerName = broker_name
        # Still missing other required props
        with pytest.raises(ValueError, match="required in type"):
            broker.to_dict()
    
    @given(
        valid_title_strategy,
        st.text(min_size=1),
        st.sampled_from(["SINGLE_INSTANCE", "ACTIVE_STANDBY_MULTI_AZ", "CLUSTER_MULTI_AZ"]),
        st.sampled_from(["ACTIVEMQ", "RABBITMQ"]),
        st.text(min_size=1),
        boolean_inputs
    )
    def test_broker_creation_with_all_required(self, title, broker_name, deployment_mode,
                                               engine_type, instance_type, publicly_accessible):
        """Property: Broker can be created with all required properties and serializes correctly"""
        broker = Broker(
            title,
            BrokerName=broker_name,
            DeploymentMode=deployment_mode,
            EngineType=engine_type,
            HostInstanceType=instance_type,
            PubliclyAccessible=publicly_accessible,
            Users=[User(Username="admin", Password="password123")]
        )
        
        # Should serialize without error
        result = broker.to_dict()
        assert isinstance(result, dict)
        assert result["Type"] == "AWS::AmazonMQ::Broker"
        assert "Properties" in result
        
        props = result["Properties"]
        assert props["BrokerName"] == broker_name
        assert props["DeploymentMode"] == deployment_mode
        assert props["EngineType"] == engine_type
        assert props["HostInstanceType"] == instance_type
        assert props["PubliclyAccessible"] == boolean(publicly_accessible)


class TestConfigurationProperties:
    """Test properties of the Configuration class"""
    
    @given(
        valid_title_strategy,
        st.text(min_size=1),
        st.sampled_from(["ACTIVEMQ", "RABBITMQ"])
    )
    def test_configuration_creation(self, title, name, engine_type):
        """Property: Configuration can be created with required properties"""
        config = Configuration(
            title,
            Name=name,
            EngineType=engine_type
        )
        
        result = config.to_dict()
        assert isinstance(result, dict)
        assert result["Type"] == "AWS::AmazonMQ::Configuration"
        assert result["Properties"]["Name"] == name
        assert result["Properties"]["EngineType"] == engine_type
    
    @given(valid_title_strategy)
    def test_configuration_missing_required(self, title):
        """Property: Configuration enforces required properties"""
        config = Configuration(title)
        with pytest.raises(ValueError, match="required in type"):
            config.to_dict()


class TestConfigurationId:
    """Test properties of ConfigurationId property class"""
    
    @given(st.text(min_size=1), st.integers())
    def test_configuration_id_creation(self, id_val, revision):
        """Property: ConfigurationId requires Id and Revision"""
        config_id = ConfigurationId(
            Id=id_val,
            Revision=revision
        )
        
        result = config_id.to_dict()
        assert result["Id"] == id_val
        assert result["Revision"] == revision
    
    @given(st.text(min_size=1))
    def test_configuration_id_missing_required(self, id_val):
        """Property: ConfigurationId enforces required properties"""
        config_id = ConfigurationId(Id=id_val)
        # Missing Revision
        with pytest.raises(ValueError, match="required in type"):
            config_id.to_dict()


class TestPropertyTypeValidation:
    """Test type validation for various property types"""
    
    @given(st.text(min_size=1), st.one_of(st.integers(), st.floats(), st.lists(st.text())))
    def test_boolean_property_type_checking(self, title, invalid_bool):
        """Property: Boolean properties reject non-boolean types"""
        assume(invalid_bool not in [True, False, 0, 1, "true", "false", "True", "False", "0", "1"])
        
        with pytest.raises((TypeError, ValueError)):
            broker = Broker(
                title,
                BrokerName="Test",
                DeploymentMode="SINGLE_INSTANCE",
                EngineType="ACTIVEMQ",
                HostInstanceType="mq.t3.micro",
                PubliclyAccessible=invalid_bool,  # Should be boolean
                Users=[User(Username="admin", Password="password123")]
            )
            broker.to_dict()
    
    @given(
        valid_title_strategy,
        st.one_of(st.integers(), st.floats(), st.booleans())
    )
    def test_string_property_type_checking(self, title, invalid_string):
        """Property: String properties reject non-string types"""
        broker = Broker(title)
        
        # BrokerName should be a string
        with pytest.raises(TypeError):
            broker.BrokerName = invalid_string
    
    @given(valid_title_strategy, st.one_of(st.text(), st.integers(), st.booleans()))
    def test_list_property_type_checking(self, title, invalid_list):
        """Property: List properties reject non-list types"""
        broker = Broker(title)
        
        # SecurityGroups should be a list
        with pytest.raises(TypeError):
            broker.SecurityGroups = invalid_list


class TestEncryptionOptions:
    """Test EncryptionOptions property class"""
    
    @given(boolean_inputs)
    def test_encryption_options_use_aws_owned_key(self, use_aws_key):
        """Property: EncryptionOptions.UseAwsOwnedKey accepts boolean values"""
        opts = EncryptionOptions(UseAwsOwnedKey=use_aws_key)
        result = opts.to_dict()
        assert result["UseAwsOwnedKey"] == boolean(use_aws_key)
    
    @given(st.text(min_size=1))
    def test_encryption_options_kms_key(self, kms_key_id):
        """Property: EncryptionOptions accepts KmsKeyId as string"""
        opts = EncryptionOptions(
            UseAwsOwnedKey=False,
            KmsKeyId=kms_key_id
        )
        result = opts.to_dict()
        assert result["KmsKeyId"] == kms_key_id
        assert result["UseAwsOwnedKey"] is False


class TestMaintenanceWindow:
    """Test MaintenanceWindow property class"""
    
    @given(
        st.sampled_from(["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]),
        st.text(min_size=1),
        st.text(min_size=1)
    )
    def test_maintenance_window_creation(self, day, time, timezone):
        """Property: MaintenanceWindow requires all three properties"""
        window = MaintenanceWindow(
            DayOfWeek=day,
            TimeOfDay=time,
            TimeZone=timezone
        )
        
        result = window.to_dict()
        assert result["DayOfWeek"] == day
        assert result["TimeOfDay"] == time
        assert result["TimeZone"] == timezone


class TestUser:
    """Test User property class"""
    
    @given(
        st.text(min_size=1),
        st.text(min_size=1),
        boolean_inputs,
        st.lists(st.text(min_size=1))
    )
    def test_user_creation(self, username, password, console_access, groups):
        """Property: User requires Username and Password, accepts optional properties"""
        user = User(
            Username=username,
            Password=password,
            ConsoleAccess=console_access,
            Groups=groups
        )
        
        result = user.to_dict()
        assert result["Username"] == username
        assert result["Password"] == password
        assert result["ConsoleAccess"] == boolean(console_access)
        assert result["Groups"] == groups


class TestTagsHandling:
    """Test Tags handling in Broker"""
    
    @given(valid_title_strategy)
    def test_broker_accepts_tags_object(self, title):
        """Property: Broker.Tags accepts Tags objects"""
        tags = Tags({"Environment": "Test", "Application": "MyApp"})
        
        broker = Broker(
            title,
            BrokerName="TestBroker",
            DeploymentMode="SINGLE_INSTANCE",
            EngineType="ACTIVEMQ",
            HostInstanceType="mq.t3.micro",
            PubliclyAccessible=True,
            Users=[User(Username="admin", Password="password123")],
            Tags=tags
        )
        
        result = broker.to_dict()
        tags_result = result["Properties"]["Tags"]
        assert isinstance(tags_result, list)
        assert len(tags_result) == 2
        
        # Tags should be sorted by key
        assert tags_result[0]["Key"] == "Application"
        assert tags_result[0]["Value"] == "MyApp"
        assert tags_result[1]["Key"] == "Environment"
        assert tags_result[1]["Value"] == "Test"
    
    @given(valid_title_strategy, st.lists(st.dictionaries(
        st.text(min_size=1), st.text(min_size=1),
        min_size=1, max_size=5
    )))
    def test_broker_accepts_list_of_tags(self, title, tags_list):
        """Property: Broker.Tags accepts list format"""
        # Convert dict to list of tag dicts
        tag_list_format = [{"Key": k, "Value": v} for d in tags_list for k, v in d.items()]
        
        broker = Broker(
            title,
            BrokerName="TestBroker",
            DeploymentMode="SINGLE_INSTANCE",
            EngineType="ACTIVEMQ",
            HostInstanceType="mq.t3.micro",
            PubliclyAccessible=True,
            Users=[User(Username="admin", Password="password123")],
            Tags=tag_list_format
        )
        
        result = broker.to_dict()
        assert result["Properties"]["Tags"] == tag_list_format
    
    @given(valid_title_strategy, st.one_of(st.integers(), st.text(), st.booleans()))
    def test_broker_rejects_invalid_tags(self, title, invalid_tags):
        """Property: Broker.Tags rejects invalid tag types"""
        with pytest.raises((TypeError, ValueError)):
            broker = Broker(
                title,
                BrokerName="TestBroker",
                DeploymentMode="SINGLE_INSTANCE",
                EngineType="ACTIVEMQ",
                HostInstanceType="mq.t3.micro",
                PubliclyAccessible=True,
                Users=[User(Username="admin", Password="password123")],
                Tags=invalid_tags
            )
            broker.to_dict()


class TestObjectEquality:
    """Test object equality properties"""
    
    @given(
        valid_title_strategy,
        st.text(min_size=1),
        st.sampled_from(["SINGLE_INSTANCE", "ACTIVE_STANDBY_MULTI_AZ"])
    )
    def test_broker_equality(self, title, broker_name, deployment_mode):
        """Property: Two Brokers with same properties should be equal"""
        broker1 = Broker(
            title,
            BrokerName=broker_name,
            DeploymentMode=deployment_mode,
            EngineType="ACTIVEMQ",
            HostInstanceType="mq.t3.micro",
            PubliclyAccessible=True,
            Users=[User(Username="admin", Password="password123")]
        )
        
        broker2 = Broker(
            title,
            BrokerName=broker_name,
            DeploymentMode=deployment_mode,
            EngineType="ACTIVEMQ",
            HostInstanceType="mq.t3.micro",
            PubliclyAccessible=True,
            Users=[User(Username="admin", Password="password123")]
        )
        
        assert broker1 == broker2
        assert broker1.to_dict() == broker2.to_dict()
    
    @given(
        valid_title_strategy,
        st.text(min_size=1).filter(lambda x: x != "TestBroker"),
        st.text(min_size=1).filter(lambda x: x != "OtherBroker")
    )
    def test_broker_inequality(self, title, name1, name2):
        """Property: Two Brokers with different properties should not be equal"""
        assume(name1 != name2)
        
        broker1 = Broker(
            title,
            BrokerName=name1,
            DeploymentMode="SINGLE_INSTANCE",
            EngineType="ACTIVEMQ",
            HostInstanceType="mq.t3.micro",
            PubliclyAccessible=True,
            Users=[User(Username="admin", Password="password123")]
        )
        
        broker2 = Broker(
            title,
            BrokerName=name2,
            DeploymentMode="SINGLE_INSTANCE",
            EngineType="ACTIVEMQ",
            HostInstanceType="mq.t3.micro",
            PubliclyAccessible=True,
            Users=[User(Username="admin", Password="password123")]
        )
        
        assert broker1 != broker2


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])