"""Test for edge cases and potential bugs in troposphere.certificatemanager"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import pytest
from troposphere import certificatemanager, Tags, Ref, AWSHelperFn


class TestEmptyStringEdgeCases:
    """Test edge cases with empty strings."""
    
    def test_empty_title_rejected(self):
        """Empty title should be rejected."""
        with pytest.raises(ValueError, match="not alphanumeric"):
            certificatemanager.Certificate(
                title="",
                DomainName="example.com"
            )
    
    def test_none_title_accepted(self):
        """None title should be accepted (for AWSProperty)."""
        # ExpiryEventsConfiguration is an AWSProperty, not AWSObject
        config = certificatemanager.ExpiryEventsConfiguration(
            DaysBeforeExpiry=30
        )
        # No exception should be raised
        assert config.title is None
    
    def test_empty_domain_name_allowed(self):
        """Empty domain name should be allowed but fail validation."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName=""
        )
        # Empty string is allowed, but might cause issues with AWS
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["DomainName"] == ""
    

class TestTypeCoercionEdgeCases:
    """Test type coercion edge cases."""
    
    def test_integer_string_coercion(self):
        """String integers should be accepted for integer fields."""
        config = certificatemanager.ExpiryEventsConfiguration(
            DaysBeforeExpiry="365"
        )
        account = certificatemanager.Account(
            title="TestAccount",
            ExpiryEventsConfiguration=config
        )
        dict_repr = account.to_dict()
        # String should be preserved
        assert dict_repr["Properties"]["ExpiryEventsConfiguration"]["DaysBeforeExpiry"] == "365"
    
    def test_negative_days_allowed(self):
        """Negative days should be allowed (validation is AWS's responsibility)."""
        config = certificatemanager.ExpiryEventsConfiguration(
            DaysBeforeExpiry=-1
        )
        account = certificatemanager.Account(
            title="TestAccount",
            ExpiryEventsConfiguration=config
        )
        dict_repr = account.to_dict()
        assert dict_repr["Properties"]["ExpiryEventsConfiguration"]["DaysBeforeExpiry"] == -1
    
    def test_float_as_integer_rejected(self):
        """Float values should be rejected for integer fields."""
        with pytest.raises((ValueError, TypeError)):
            config = certificatemanager.ExpiryEventsConfiguration(
                DaysBeforeExpiry=3.14
            )
            account = certificatemanager.Account(
                title="TestAccount",
                ExpiryEventsConfiguration=config
            )
            account.to_dict()


class TestListPropertyEdgeCases:
    """Test edge cases with list properties."""
    
    def test_empty_subject_alternative_names(self):
        """Empty SubjectAlternativeNames list should be allowed."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            SubjectAlternativeNames=[]
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["SubjectAlternativeNames"] == []
    
    def test_duplicate_subject_alternative_names(self):
        """Duplicate SANs should be allowed (AWS will handle validation)."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            SubjectAlternativeNames=["sub.example.com", "sub.example.com"]
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["SubjectAlternativeNames"] == ["sub.example.com", "sub.example.com"]
    
    def test_empty_domain_validation_options(self):
        """Empty DomainValidationOptions list should be allowed."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            DomainValidationOptions=[]
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["DomainValidationOptions"] == []


class TestReferenceEdgeCases:
    """Test edge cases with references."""
    
    def test_ref_to_nonexistent_resource(self):
        """Ref to non-existent resource should be allowed (AWS will validate)."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName=Ref("NonExistentParameter")
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["DomainName"] == {"Ref": "NonExistentParameter"}
    
    def test_circular_ref_allowed(self):
        """Circular reference to self should be allowed syntactically."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com"
        )
        # Reference to self - AWS will catch this
        cert.CertificateAuthorityArn = cert.ref()
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["CertificateAuthorityArn"] == {"Ref": "TestCert"}


class TestUnicodeAndSpecialCharacters:
    """Test Unicode and special character handling."""
    
    def test_unicode_in_domain_name(self):
        """Unicode domain names should be allowed."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="例え.jp"
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["DomainName"] == "例え.jp"
    
    def test_special_chars_in_validation_domain(self):
        """Special characters in validation domain should be preserved."""
        option = certificatemanager.DomainValidationOption(
            DomainName="*.example.com",
            ValidationDomain="admin@example.com"
        )
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="*.example.com",
            DomainValidationOptions=[option]
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["DomainValidationOptions"][0]["ValidationDomain"] == "admin@example.com"


class TestPropertyOverwriting:
    """Test property overwriting behavior."""
    
    def test_property_overwrite(self):
        """Properties should be overwritable."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="first.com"
        )
        cert.DomainName = "second.com"
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["DomainName"] == "second.com"
    
    def test_multiple_property_overwrites(self):
        """Multiple overwrites should use the last value."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="first.com"
        )
        cert.DomainName = "second.com"
        cert.DomainName = "third.com"
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["DomainName"] == "third.com"


class TestTagsEdgeCases:
    """Test edge cases with Tags."""
    
    def test_empty_tags(self):
        """Empty Tags object should be allowed."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            Tags=Tags()
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["Tags"] == []
    
    def test_tags_with_empty_key(self):
        """Tags with empty keys should be allowed (AWS will validate)."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            Tags=Tags(**{"": "value"})
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["Tags"] == [{"Key": "", "Value": "value"}]
    
    def test_tags_with_none_value(self):
        """Tags with None values should be preserved."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            Tags=Tags(key=None)
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["Tags"] == [{"Key": "key", "Value": None}]
    
    def test_tags_concatenation(self):
        """Tags should support concatenation."""
        tags1 = Tags(env="prod")
        tags2 = Tags(team="security")
        combined = tags1 + tags2
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            Tags=combined
        )
        dict_repr = cert.to_dict()
        # Combined tags should have both
        assert len(dict_repr["Properties"]["Tags"]) == 2
        tag_dict = {tag["Key"]: tag["Value"] for tag in dict_repr["Properties"]["Tags"]}
        assert tag_dict == {"env": "prod", "team": "security"}


class TestValidationMethodEdgeCases:
    """Test ValidationMethod edge cases."""
    
    def test_invalid_validation_method_allowed(self):
        """Invalid ValidationMethod should be allowed (AWS will validate)."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            ValidationMethod="INVALID_METHOD"
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["ValidationMethod"] == "INVALID_METHOD"
    
    def test_mixed_case_validation_method(self):
        """Mixed case validation methods should be preserved."""
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName="example.com",
            ValidationMethod="DnS"  # Should be DNS
        )
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["ValidationMethod"] == "DnS"