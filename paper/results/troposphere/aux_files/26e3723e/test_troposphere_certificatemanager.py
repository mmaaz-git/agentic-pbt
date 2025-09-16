"""Property-based tests for troposphere.certificatemanager module."""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings, example
import pytest
from troposphere import certificatemanager, Tags, AWSHelperFn
from troposphere import BaseAWSObject, Ref, If


# Strategy for valid alphanumeric titles
def valid_title_strategy():
    return st.text(alphabet=st.characters(whitelist_categories=(), whitelist_characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"), min_size=1, max_size=50)

# Strategy for invalid titles (containing non-alphanumeric)
def invalid_title_strategy():
    return st.text(min_size=1, max_size=50).filter(
        lambda s: not re.match(r'^[a-zA-Z0-9]+$', s) and s != ""
    )

# Strategy for domain names
def domain_name_strategy():
    return st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50).map(
        lambda s: f"{s}.example.com"
    )

# Strategy for generating valid Tags
def tags_strategy():
    tag_dict = st.dictionaries(
        st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20),
        st.text(min_size=1, max_size=50),
        min_size=0, 
        max_size=5
    )
    return st.one_of(
        tag_dict.map(lambda d: Tags(**d)),
        tag_dict.map(lambda d: [{"Key": k, "Value": v} for k, v in d.items()]),
    )


class TestTitleValidation:
    """Test the title validation property."""
    
    @given(title=valid_title_strategy())
    def test_valid_titles_accepted(self, title):
        """Valid alphanumeric titles should be accepted."""
        cert = certificatemanager.Certificate(
            title=title,
            DomainName="example.com"
        )
        assert cert.title == title
    
    @given(title=invalid_title_strategy())
    def test_invalid_titles_rejected(self, title):
        """Non-alphanumeric titles should raise ValueError."""
        with pytest.raises(ValueError, match="not alphanumeric"):
            certificatemanager.Certificate(
                title=title,
                DomainName="example.com"
            )


class TestRequiredProperties:
    """Test required property validation."""
    
    @given(title=valid_title_strategy())
    def test_certificate_requires_domain_name(self, title):
        """Certificate without DomainName should fail validation."""
        cert = certificatemanager.Certificate(title=title)
        with pytest.raises(ValueError, match="DomainName required"):
            cert.to_dict()
    
    @given(title=valid_title_strategy())
    def test_account_requires_expiry_config(self, title):
        """Account without ExpiryEventsConfiguration should fail validation."""
        account = certificatemanager.Account(title=title)
        with pytest.raises(ValueError, match="ExpiryEventsConfiguration required"):
            account.to_dict()
    
    @given(title=valid_title_strategy(), domain=domain_name_strategy())
    def test_domain_validation_requires_domain_name(self, title, domain):
        """DomainValidationOption without DomainName should fail validation."""
        cert = certificatemanager.Certificate(
            title=title,
            DomainName=domain,
            DomainValidationOptions=[
                certificatemanager.DomainValidationOption()
            ]
        )
        with pytest.raises(ValueError, match="DomainName required"):
            cert.to_dict()


class TestTypeValidation:
    """Test property type validation."""
    
    @given(title=valid_title_strategy(), days=st.one_of(st.integers(), st.from_regex(r'^\d+$', fullmatch=True)))
    def test_integer_property_accepts_int_or_numeric_string(self, title, days):
        """DaysBeforeExpiry should accept integers or numeric strings."""
        config = certificatemanager.ExpiryEventsConfiguration(
            DaysBeforeExpiry=days
        )
        account = certificatemanager.Account(
            title=title,
            ExpiryEventsConfiguration=config
        )
        assert account.to_dict() is not None
    
    @given(title=valid_title_strategy(), days=st.text().filter(lambda s: not s.isdigit()))
    def test_integer_property_rejects_non_numeric(self, title, days):
        """DaysBeforeExpiry should reject non-numeric strings."""
        with pytest.raises((ValueError, TypeError)):
            config = certificatemanager.ExpiryEventsConfiguration(
                DaysBeforeExpiry=days
            )
            account = certificatemanager.Account(
                title=title,
                ExpiryEventsConfiguration=config
            )
            account.to_dict()
    
    @given(title=valid_title_strategy(), tags=tags_strategy())
    def test_tags_accepts_valid_types(self, title, tags):
        """Tags property should accept Tags objects or lists."""
        cert = certificatemanager.Certificate(
            title=title,
            DomainName="example.com",
            Tags=tags
        )
        assert cert.to_dict() is not None
    
    @given(title=valid_title_strategy(), invalid_tags=st.one_of(
        st.integers(),
        st.floats(),
        st.text(),
        st.dictionaries(st.text(), st.text())
    ))
    def test_tags_rejects_invalid_types(self, title, invalid_tags):
        """Tags property should reject invalid types."""
        with pytest.raises((ValueError, TypeError)):
            cert = certificatemanager.Certificate(
                title=title,
                DomainName="example.com",
                Tags=invalid_tags
            )
            cert.to_dict()


class TestSerializationRoundTrip:
    """Test serialization round-trip properties."""
    
    @given(title=valid_title_strategy(), domain=domain_name_strategy())
    def test_certificate_dict_round_trip(self, title, domain):
        """Certificate should survive to_dict/from_dict round trip."""
        cert1 = certificatemanager.Certificate(
            title=title,
            DomainName=domain,
            ValidationMethod="DNS"
        )
        
        dict_repr = cert1.to_dict()
        cert2 = certificatemanager.Certificate.from_dict(
            title=title,
            d=dict_repr["Properties"]
        )
        
        # Compare the dict representations
        assert cert1.to_dict() == cert2.to_dict()
    
    @given(title=valid_title_strategy(), days=st.integers(min_value=1, max_value=365))
    def test_account_dict_round_trip(self, title, days):
        """Account should survive to_dict/from_dict round trip."""
        account1 = certificatemanager.Account(
            title=title,
            ExpiryEventsConfiguration=certificatemanager.ExpiryEventsConfiguration(
                DaysBeforeExpiry=days
            )
        )
        
        dict_repr = account1.to_dict()
        account2 = certificatemanager.Account.from_dict(
            title=title,
            d=dict_repr["Properties"]
        )
        
        assert account1.to_dict() == account2.to_dict()


class TestEqualityProperties:
    """Test object equality properties."""
    
    @given(title=valid_title_strategy(), domain=domain_name_strategy())
    def test_equal_certificates_are_equal(self, title, domain):
        """Two certificates with same properties should be equal."""
        cert1 = certificatemanager.Certificate(
            title=title,
            DomainName=domain
        )
        cert2 = certificatemanager.Certificate(
            title=title,
            DomainName=domain
        )
        
        assert cert1 == cert2
        assert hash(cert1) == hash(cert2)
    
    @given(
        title1=valid_title_strategy(),
        title2=valid_title_strategy(),
        domain=domain_name_strategy()
    )
    def test_different_titles_make_unequal(self, title1, title2, domain):
        """Certificates with different titles should not be equal."""
        assume(title1 != title2)
        
        cert1 = certificatemanager.Certificate(
            title=title1,
            DomainName=domain
        )
        cert2 = certificatemanager.Certificate(
            title=title2,
            DomainName=domain
        )
        
        assert cert1 != cert2
    
    @given(
        title=valid_title_strategy(),
        domain1=domain_name_strategy(),
        domain2=domain_name_strategy()
    )
    def test_different_properties_make_unequal(self, title, domain1, domain2):
        """Certificates with different properties should not be equal."""
        assume(domain1 != domain2)
        
        cert1 = certificatemanager.Certificate(
            title=title,
            DomainName=domain1
        )
        cert2 = certificatemanager.Certificate(
            title=title,
            DomainName=domain2
        )
        
        assert cert1 != cert2


class TestAWSHelperFnIntegration:
    """Test integration with AWS helper functions."""
    
    @given(title=valid_title_strategy(), condition_name=valid_title_strategy())
    def test_certificate_with_ref_domain(self, title, condition_name):
        """Certificate should accept Ref for DomainName."""
        cert = certificatemanager.Certificate(
            title=title,
            DomainName=Ref(condition_name)
        )
        dict_repr = cert.to_dict()
        assert "Ref" in str(dict_repr)
    
    @given(
        title=valid_title_strategy(),
        cond=valid_title_strategy(),
        domain1=domain_name_strategy(),
        domain2=domain_name_strategy()
    )
    def test_certificate_with_if_condition(self, title, cond, domain1, domain2):
        """Certificate should accept If conditions for properties."""
        cert = certificatemanager.Certificate(
            title=title,
            DomainName=If(cond, domain1, domain2)
        )
        dict_repr = cert.to_dict()
        assert "Fn::If" in str(dict_repr)


class TestDomainValidationOption:
    """Test DomainValidationOption properties."""
    
    @given(domain=domain_name_strategy(), hosted_zone=st.text(min_size=1, max_size=50))
    def test_domain_validation_with_all_properties(self, domain, hosted_zone):
        """DomainValidationOption should accept all valid properties."""
        option = certificatemanager.DomainValidationOption(
            DomainName=domain,
            HostedZoneId=hosted_zone,
            ValidationDomain=domain
        )
        
        # Create certificate with this option
        cert = certificatemanager.Certificate(
            title="TestCert",
            DomainName=domain,
            DomainValidationOptions=[option]
        )
        
        dict_repr = cert.to_dict()
        assert dict_repr["Properties"]["DomainValidationOptions"][0]["DomainName"] == domain
        assert dict_repr["Properties"]["DomainValidationOptions"][0]["HostedZoneId"] == hosted_zone


class TestSubjectAlternativeNames:
    """Test SubjectAlternativeNames property."""
    
    @given(
        title=valid_title_strategy(),
        main_domain=domain_name_strategy(),
        san_domains=st.lists(domain_name_strategy(), min_size=0, max_size=5)
    )
    def test_subject_alternative_names_as_list(self, title, main_domain, san_domains):
        """SubjectAlternativeNames should accept list of strings."""
        cert = certificatemanager.Certificate(
            title=title,
            DomainName=main_domain,
            SubjectAlternativeNames=san_domains
        )
        
        dict_repr = cert.to_dict()
        if san_domains:
            assert dict_repr["Properties"]["SubjectAlternativeNames"] == san_domains