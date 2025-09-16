#!/usr/bin/env python3
"""Edge case property-based tests for troposphere.acmpca module"""

import sys
import math
from hypothesis import given, strategies as st, assume, settings, example
import pytest

# Add the site-packages to path to import troposphere
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.acmpca import (
    Validity, Certificate, CertificateAuthority,
    Subject, CustomAttribute, KeyUsage, GeneralName,
    ExtendedKeyUsage, Extensions, ApiPassthrough,
    CustomExtension, EdiPartyName, OtherName
)
from troposphere.validators.acmpca import (
    validate_validity_type,
    validate_signing_algorithm,
    validate_key_algorithm,
    validate_certificateauthority_type
)
from troposphere.validators import double, boolean, integer


# Test 1: Empty string handling in validators
def test_validators_empty_string():
    """Validators should reject empty strings"""
    with pytest.raises(ValueError):
        validate_validity_type("")
    with pytest.raises(ValueError):
        validate_signing_algorithm("")
    with pytest.raises(ValueError):
        validate_key_algorithm("")
    with pytest.raises(ValueError):
        validate_certificateauthority_type("")


# Test 2: None handling in validators
def test_validators_none():
    """Validators should handle None appropriately"""
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_validity_type(None)
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_signing_algorithm(None)


# Test 3: Unicode edge cases in validators
@given(st.text(alphabet="αβγδεζηθικλμνξοπρστυφχψω", min_size=1))
def test_validators_unicode(text):
    """Validators should reject non-ASCII text"""
    with pytest.raises(ValueError):
        validate_validity_type(text)


# Test 4: Validator with numeric input
@given(st.integers())
def test_validators_numeric_input(num):
    """Validators should handle numeric inputs"""
    with pytest.raises((ValueError, AttributeError, TypeError)):
        validate_validity_type(num)


# Test 5: Boolean validator edge cases
def test_boolean_validator():
    """Boolean validator should handle various inputs"""
    assert boolean(True) == True
    assert boolean(False) == False
    assert boolean(1) == True
    assert boolean(0) == False
    assert boolean("true") == True
    assert boolean("false") == False
    assert boolean("True") == True
    assert boolean("False") == False
    
    # These should raise exceptions
    with pytest.raises((ValueError, TypeError)):
        boolean("maybe")
    with pytest.raises((ValueError, TypeError)):
        boolean(None)


# Test 6: Integer validator edge cases
def test_integer_validator():
    """Integer validator should handle various inputs"""
    assert integer(42) == 42
    assert integer(0) == 0
    assert integer(-100) == -100
    assert integer("42") == 42
    assert integer("-100") == -100
    
    # These should raise exceptions
    with pytest.raises((ValueError, TypeError)):
        integer("not_a_number")
    with pytest.raises((ValueError, TypeError)):
        integer(3.14)
    with pytest.raises((ValueError, TypeError)):
        integer(None)


# Test 7: Double validator edge cases
def test_double_validator_edge_cases():
    """Double validator should handle edge cases"""
    assert double(0) == 0
    assert double(0.0) == 0.0
    assert double(-0.0) == -0.0
    assert double("3.14") == 3.14
    assert double("42") == 42
    
    # Special float values
    with pytest.raises((ValueError, TypeError)):
        double(float('nan'))
    with pytest.raises((ValueError, TypeError)):
        double(float('inf'))
    with pytest.raises((ValueError, TypeError)):
        double(float('-inf'))


# Test 8: CustomExtension with edge case values
@given(
    critical=st.one_of(st.just(None), st.booleans()),
    object_id=st.text(min_size=1),
    value=st.text()
)
def test_custom_extension_edge_cases(critical, object_id, value):
    """CustomExtension should handle various input combinations"""
    kwargs = {
        "ObjectIdentifier": object_id,
        "Value": value
    }
    if critical is not None:
        kwargs["Critical"] = critical
    
    ext = CustomExtension(**kwargs)
    assert ext.properties["ObjectIdentifier"] == object_id
    assert ext.properties["Value"] == value
    if critical is not None:
        assert ext.properties.get("Critical") == critical


# Test 9: Subject with all fields populated
@given(
    common_name=st.text(min_size=1, max_size=64),
    country=st.text(min_size=2, max_size=2, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    state=st.text(min_size=1, max_size=128),
    locality=st.text(min_size=1, max_size=128),
    organization=st.text(min_size=1, max_size=64),
    organizational_unit=st.text(min_size=1, max_size=64),
    distinguished_name_qualifier=st.text(min_size=1, max_size=64),
    generation_qualifier=st.text(min_size=1, max_size=3),
    given_name=st.text(min_size=1, max_size=16),
    initials=st.text(min_size=1, max_size=5),
    pseudonym=st.text(min_size=1, max_size=128),
    serial_number=st.text(min_size=1, max_size=64),
    surname=st.text(min_size=1, max_size=40),
    title=st.text(min_size=1, max_size=64)
)
def test_subject_all_fields(
    common_name, country, state, locality, organization, organizational_unit,
    distinguished_name_qualifier, generation_qualifier, given_name, initials,
    pseudonym, serial_number, surname, title
):
    """Subject should accept all possible fields"""
    subject = Subject(
        CommonName=common_name,
        Country=country,
        State=state,
        Locality=locality,
        Organization=organization,
        OrganizationalUnit=organizational_unit,
        DistinguishedNameQualifier=distinguished_name_qualifier,
        GenerationQualifier=generation_qualifier,
        GivenName=given_name,
        Initials=initials,
        Pseudonym=pseudonym,
        SerialNumber=serial_number,
        Surname=surname,
        Title=title
    )
    
    assert subject.properties["CommonName"] == common_name
    assert subject.properties["Country"] == country
    assert subject.properties["State"] == state
    assert subject.properties["Locality"] == locality
    assert subject.properties["Organization"] == organization
    assert subject.properties["OrganizationalUnit"] == organizational_unit
    assert subject.properties["DistinguishedNameQualifier"] == distinguished_name_qualifier
    assert subject.properties["GenerationQualifier"] == generation_qualifier
    assert subject.properties["GivenName"] == given_name
    assert subject.properties["Initials"] == initials
    assert subject.properties["Pseudonym"] == pseudonym
    assert subject.properties["SerialNumber"] == serial_number
    assert subject.properties["Surname"] == surname
    assert subject.properties["Title"] == title


# Test 10: CustomAttribute handling
@given(
    object_id=st.text(min_size=1),
    value=st.text()
)
def test_custom_attribute(object_id, value):
    """CustomAttribute should handle required fields"""
    attr = CustomAttribute(ObjectIdentifier=object_id, Value=value)
    assert attr.properties["ObjectIdentifier"] == object_id
    assert attr.properties["Value"] == value


# Test 11: Subject with CustomAttributes list
@given(
    common_name=st.text(min_size=1, max_size=64),
    custom_attrs=st.lists(
        st.tuples(st.text(min_size=1), st.text()),
        min_size=0,
        max_size=5
    )
)
def test_subject_with_custom_attributes(common_name, custom_attrs):
    """Subject should accept CustomAttributes list"""
    custom_attribute_objects = [
        CustomAttribute(ObjectIdentifier=oid, Value=val)
        for oid, val in custom_attrs
    ]
    
    subject = Subject(
        CommonName=common_name,
        CustomAttributes=custom_attribute_objects if custom_attribute_objects else None
    )
    
    assert subject.properties["CommonName"] == common_name
    if custom_attribute_objects:
        assert subject.properties.get("CustomAttributes") == custom_attribute_objects


# Test 12: KeyUsage with all boolean fields
@given(
    crl_sign=st.booleans(),
    data_encipherment=st.booleans(),
    decipher_only=st.booleans(),
    digital_signature=st.booleans(),
    encipher_only=st.booleans(),
    key_agreement=st.booleans(),
    key_cert_sign=st.booleans(),
    key_encipherment=st.booleans(),
    non_repudiation=st.booleans()
)
def test_key_usage_all_fields(
    crl_sign, data_encipherment, decipher_only, digital_signature,
    encipher_only, key_agreement, key_cert_sign, key_encipherment,
    non_repudiation
):
    """KeyUsage should accept all boolean fields"""
    key_usage = KeyUsage(
        CRLSign=crl_sign,
        DataEncipherment=data_encipherment,
        DecipherOnly=decipher_only,
        DigitalSignature=digital_signature,
        EncipherOnly=encipher_only,
        KeyAgreement=key_agreement,
        KeyCertSign=key_cert_sign,
        KeyEncipherment=key_encipherment,
        NonRepudiation=non_repudiation
    )
    
    assert key_usage.properties.get("CRLSign") == crl_sign
    assert key_usage.properties.get("DataEncipherment") == data_encipherment
    assert key_usage.properties.get("DecipherOnly") == decipher_only
    assert key_usage.properties.get("DigitalSignature") == digital_signature
    assert key_usage.properties.get("EncipherOnly") == encipher_only
    assert key_usage.properties.get("KeyAgreement") == key_agreement
    assert key_usage.properties.get("KeyCertSign") == key_cert_sign
    assert key_usage.properties.get("KeyEncipherment") == key_encipherment
    assert key_usage.properties.get("NonRepudiation") == non_repudiation


# Test 13: EdiPartyName properties
@given(
    party_name=st.text(min_size=1),
    name_assigner=st.one_of(st.none(), st.text(min_size=1))
)
def test_edi_party_name(party_name, name_assigner):
    """EdiPartyName should handle required and optional fields"""
    kwargs = {"PartyName": party_name}
    if name_assigner is not None:
        kwargs["NameAssigner"] = name_assigner
    
    edi = EdiPartyName(**kwargs)
    assert edi.properties["PartyName"] == party_name
    if name_assigner is not None:
        assert edi.properties.get("NameAssigner") == name_assigner


# Test 14: OtherName properties
@given(
    type_id=st.text(min_size=1),
    value=st.text()
)
def test_other_name(type_id, value):
    """OtherName should handle required fields"""
    other = OtherName(TypeId=type_id, Value=value)
    assert other.properties["TypeId"] == type_id
    assert other.properties["Value"] == value


# Test 15: GeneralName with different field combinations
@given(
    dns_name=st.one_of(st.none(), st.text(min_size=1)),
    ip_address=st.one_of(st.none(), st.text(min_size=7, max_size=15).filter(lambda x: '.' in x)),
    rfc822_name=st.one_of(st.none(), st.text(min_size=1).filter(lambda x: '@' not in x or '@' in x)),
    uri=st.one_of(st.none(), st.text(min_size=1))
)
def test_general_name_combinations(dns_name, ip_address, rfc822_name, uri):
    """GeneralName should handle multiple optional fields"""
    kwargs = {}
    if dns_name is not None:
        kwargs["DnsName"] = dns_name
    if ip_address is not None:
        kwargs["IpAddress"] = ip_address
    if rfc822_name is not None:
        kwargs["Rfc822Name"] = rfc822_name
    if uri is not None:
        kwargs["UniformResourceIdentifier"] = uri
    
    # GeneralName requires at least one field
    if kwargs:
        gn = GeneralName(**kwargs)
        if dns_name is not None:
            assert gn.properties.get("DnsName") == dns_name
        if ip_address is not None:
            assert gn.properties.get("IpAddress") == ip_address
        if rfc822_name is not None:
            assert gn.properties.get("Rfc822Name") == rfc822_name
        if uri is not None:
            assert gn.properties.get("UniformResourceIdentifier") == uri


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])