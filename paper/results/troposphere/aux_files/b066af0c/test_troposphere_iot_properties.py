#!/usr/bin/env python3
"""Property-based tests for troposphere.iot module"""

import string
from hypothesis import assume, given, strategies as st, settings
import troposphere.iot as iot
from troposphere import Ref, GetAtt, Tags
import pytest


# Strategy for valid resource titles (alphanumeric only)
valid_titles = st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=50)

# Strategy for invalid titles (containing non-alphanumeric characters)
invalid_titles = st.text(min_size=1, max_size=50).filter(
    lambda s: not s.isalnum() and len(s) > 0
)

# Strategy for strings
safe_strings = st.text(min_size=0, max_size=100, alphabet=string.printable)

# Strategy for booleans  
bools = st.booleans()

# Strategy for integers
ints = st.integers(min_value=-1000000, max_value=1000000)

# Strategy for doubles
doubles = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)


class TestTitleValidation:
    """Test property: Resource titles must be alphanumeric"""
    
    @given(title=valid_titles)
    def test_valid_titles_accepted(self, title):
        """Valid alphanumeric titles should be accepted"""
        # Use Certificate as a simple resource with required properties
        cert = iot.Certificate(title=title, Status="ACTIVE")
        assert cert.title == title
    
    @given(title=invalid_titles)
    def test_invalid_titles_rejected(self, title):
        """Non-alphanumeric titles should be rejected"""
        with pytest.raises(ValueError, match="not alphanumeric"):
            iot.Certificate(title=title, Status="ACTIVE")
    
    @given(st.text(min_size=0, max_size=50))
    def test_empty_or_whitespace_title_rejected(self, title):
        """Empty or whitespace-only titles should be rejected"""
        assume(not title or not title.strip() or not title.isalnum())
        if title:  # Non-empty invalid title
            with pytest.raises(ValueError, match="not alphanumeric"):
                iot.Certificate(title=title, Status="ACTIVE")


class TestRequiredProperties:
    """Test property: Required properties must be present"""
    
    @given(title=valid_titles)
    def test_certificate_requires_status(self, title):
        """Certificate requires Status property"""
        cert = iot.Certificate(title=title, Status="ACTIVE")
        # Should succeed with required property
        cert.to_dict()
        
    @given(title=valid_titles)
    def test_certificate_missing_required_raises(self, title):
        """Certificate without Status should raise on to_dict()"""
        cert = iot.Certificate(title=title)
        with pytest.raises(ValueError, match="Resource Status required"):
            cert.to_dict()
    
    @given(title=valid_titles, account_id=safe_strings, role_arn=safe_strings)
    def test_account_audit_config_required_props(self, title, account_id, role_arn):
        """AccountAuditConfiguration requires multiple properties"""
        # Create minimal valid AuditCheckConfigurations
        audit_checks = iot.AuditCheckConfigurations()
        
        # Missing required properties should raise
        config = iot.AccountAuditConfiguration(title=title)
        with pytest.raises(ValueError, match="Resource .* required"):
            config.to_dict()
        
        # With all required properties should work
        config = iot.AccountAuditConfiguration(
            title=title,
            AccountId=account_id,
            AuditCheckConfigurations=audit_checks,
            RoleArn=role_arn
        )
        config.to_dict()  # Should not raise


class TestTypeValidation:
    """Test property: Properties must match their declared types"""
    
    @given(title=valid_titles, enabled=bools)
    def test_boolean_property_validation(self, title, enabled):
        """Boolean properties should accept bool values"""
        # AuditCheckConfiguration has Enabled as boolean
        config = iot.AuditCheckConfiguration(Enabled=enabled)
        assert config.properties.get("Enabled") == enabled
    
    @given(title=valid_titles, value=st.one_of(safe_strings, ints, st.floats(), st.lists(st.integers())))
    def test_boolean_property_wrong_type(self, title, value):
        """Boolean properties should reject non-bool values"""
        assume(not isinstance(value, bool))
        config = iot.AuditCheckConfiguration()
        with pytest.raises(TypeError):
            config.Enabled = value
    
    @given(title=valid_titles, threshold=ints)
    def test_integer_property_validation(self, title, threshold):
        """Integer properties should accept integer values"""
        # InProgressTimeoutInMinutes is an integer property
        timeout = iot.TimeoutConfig(InProgressTimeoutInMinutes=threshold)
        assert timeout.properties.get("InProgressTimeoutInMinutes") == threshold
    
    @given(title=valid_titles, names=st.lists(safe_strings, min_size=1, max_size=5))
    def test_list_property_validation(self, title, names):
        """List properties should accept lists of correct type"""
        # ThingGroupNames is a list of strings
        params = iot.AddThingsToThingGroupParams(ThingGroupNames=names)
        assert params.properties.get("ThingGroupNames") == names


class TestPropertyAccess:
    """Test invariant: Properties set should be retrievable"""
    
    @given(title=valid_titles, description=safe_strings)
    def test_set_and_get_property(self, title, description):
        """Properties set on creation should be retrievable"""
        # BillingGroupProperties has BillingGroupDescription property
        props = iot.BillingGroupProperties(BillingGroupDescription=description)
        assert props.BillingGroupDescription == description
        assert props.properties["BillingGroupDescription"] == description
    
    @given(title=valid_titles, status=st.sampled_from(["ACTIVE", "INACTIVE", "REVOKED", "PENDING_TRANSFER"]))
    def test_certificate_status_property(self, title, status):
        """Certificate Status property should be settable and retrievable"""
        cert = iot.Certificate(title=title, Status=status)
        assert cert.Status == status
        
        # Should be in the to_dict output
        output = cert.to_dict()
        assert output["Properties"]["Status"] == status


class TestRoundTripSerialization:
    """Test property: to_dict() and from_dict() should be inverses"""
    
    @given(title=valid_titles, name=safe_strings)
    def test_simple_resource_round_trip(self, title, name):
        """Simple resources should survive round-trip serialization"""
        # Create a Thing with AttributePayload
        thing = iot.Thing(title=title, ThingName=name)
        
        # Convert to dict
        thing_dict = thing.to_dict()
        
        # Create from dict - should be equivalent
        thing2 = iot.Thing.from_dict(title=title, d=thing_dict["Properties"])
        
        # Properties should match
        assert thing2.properties.get("ThingName") == name
        assert thing.to_dict() == thing2.to_dict()
    
    @given(title=valid_titles, 
           group_name=safe_strings,
           group_desc=safe_strings)
    def test_nested_property_round_trip(self, title, group_name, group_desc):
        """Resources with nested properties should survive round-trip"""
        # Create BillingGroup with nested BillingGroupProperties
        props = iot.BillingGroupProperties(BillingGroupDescription=group_desc)
        group = iot.BillingGroup(
            title=title,
            BillingGroupName=group_name,
            BillingGroupProperties=props
        )
        
        # Convert to dict
        group_dict = group.to_dict()
        
        # Create from dict
        group2 = iot.BillingGroup.from_dict(title=title, d=group_dict["Properties"])
        
        # Should have same properties
        assert group2.BillingGroupName == group_name
        assert group2.BillingGroupProperties.BillingGroupDescription == group_desc
        assert group.to_dict() == group2.to_dict()


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @given(title=valid_titles)
    def test_optional_properties_can_be_omitted(self, title):
        """Optional properties should not be required"""
        # Certificate has optional properties like CertificateMode
        cert = iot.Certificate(title=title, Status="ACTIVE")
        cert.to_dict()  # Should not raise
        
    @given(title=valid_titles)
    def test_empty_string_properties(self, title):
        """Empty strings should be valid for string properties"""
        # Empty string for optional property
        thing = iot.Thing(title=title, ThingName="")
        assert thing.ThingName == ""
        output = thing.to_dict()
        assert output["Properties"]["ThingName"] == ""
    
    @given(title=valid_titles, dims=st.lists(safe_strings, min_size=1, max_size=10))
    def test_dimension_stringvalues_required(self, title, dims):
        """Dimension requires StringValues list"""
        # Dimension requires both StringValues and Type
        dim = iot.Dimension(title=title, StringValues=dims, Type="TOPIC_FILTER")
        output = dim.to_dict()
        assert output["Properties"]["StringValues"] == dims
        
        # Missing StringValues should raise
        dim2 = iot.Dimension(title=title, Type="TOPIC_FILTER")
        with pytest.raises(ValueError, match="Resource StringValues required"):
            dim2.to_dict()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])