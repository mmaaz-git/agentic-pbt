#!/usr/bin/env python3
"""Property-based tests for troposphere.acmpca module"""

import sys
import math
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the site-packages to path to import troposphere
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.acmpca import (
    Validity, Certificate, CertificateAuthority,
    Subject, CustomAttribute, KeyUsage, GeneralName,
    ExtendedKeyUsage, Extensions, ApiPassthrough
)
from troposphere.validators.acmpca import (
    validate_validity_type,
    validate_signing_algorithm,
    validate_key_algorithm,
    validate_certificateauthority_type
)
from troposphere.validators import double


# Test 1: Validator round-trip invariant - valid inputs should be returned unchanged
@given(st.sampled_from(["ABSOLUTE", "DAYS", "END_DATE", "MONTHS", "YEARS"]))
def test_validity_type_round_trip(validity_type):
    """Valid validity types should be returned unchanged"""
    result = validate_validity_type(validity_type)
    assert result == validity_type


@given(st.sampled_from([
    "SHA256WITHECDSA", "SHA256WITHRSA", "SHA384WITHECDSA",
    "SHA384WITHRSA", "SHA512WITHECDSA", "SHA512WITHRSA"
]))
def test_signing_algorithm_round_trip(signing_algorithm):
    """Valid signing algorithms should be returned unchanged"""
    result = validate_signing_algorithm(signing_algorithm)
    assert result == signing_algorithm


@given(st.sampled_from(["EC_prime256v1", "EC_secp384r1", "RSA_2048", "RSA_4096"]))
def test_key_algorithm_round_trip(key_algorithm):
    """Valid key algorithms should be returned unchanged"""
    result = validate_key_algorithm(key_algorithm)
    assert result == key_algorithm


@given(st.sampled_from(["ROOT", "SUBORDINATE"]))
def test_certificateauthority_type_round_trip(ca_type):
    """Valid CA types should be returned unchanged"""
    result = validate_certificateauthority_type(ca_type)
    assert result == ca_type


# Test 2: Validator rejection property - invalid inputs should raise ValueError
@given(st.text().filter(lambda x: x not in ["ABSOLUTE", "DAYS", "END_DATE", "MONTHS", "YEARS"]))
def test_validity_type_rejects_invalid(invalid_type):
    """Invalid validity types should raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        validate_validity_type(invalid_type)
    assert "Certificate Validity Type must be one of:" in str(exc_info.value)


@given(st.text().filter(lambda x: x not in [
    "SHA256WITHECDSA", "SHA256WITHRSA", "SHA384WITHECDSA",
    "SHA384WITHRSA", "SHA512WITHECDSA", "SHA512WITHRSA"
]))
def test_signing_algorithm_rejects_invalid(invalid_algo):
    """Invalid signing algorithms should raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        validate_signing_algorithm(invalid_algo)
    assert "Certificate SigningAlgorithm must be one of:" in str(exc_info.value)


# Test 3: Case sensitivity property - validators should be case-sensitive
@given(st.sampled_from(["DAYS", "MONTHS", "YEARS"]))
def test_validity_type_case_sensitive(valid_type):
    """Validators should be case-sensitive"""
    lowercase = valid_type.lower()
    if lowercase != valid_type:  # Only test if different
        with pytest.raises(ValueError):
            validate_validity_type(lowercase)


# Test 4: Edge cases for validators with string mutations
@given(st.sampled_from(["ROOT", "SUBORDINATE"]))
def test_certificateauthority_type_with_spaces(ca_type):
    """Validators should reject values with extra spaces"""
    with_spaces = " " + ca_type + " "
    with pytest.raises(ValueError):
        validate_certificateauthority_type(with_spaces)


# Test 5: Validity class with double validation
@given(
    validity_type=st.sampled_from(["DAYS", "MONTHS", "YEARS"]),
    value=st.floats(min_value=0.1, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_validity_accepts_valid_doubles(validity_type, value):
    """Validity should accept valid double values"""
    validity = Validity(Type=validity_type, Value=value)
    assert validity.properties["Type"] == validity_type
    assert validity.properties["Value"] == value


# Test 6: Double validator behavior
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308))
def test_double_validator_floats(value):
    """Double validator should accept finite floats"""
    result = double(value)
    assert result == value


@given(st.integers(min_value=-10**15, max_value=10**15))
def test_double_validator_integers(value):
    """Double validator should accept integers as doubles"""
    result = double(value)
    assert result == value


# Test 7: Subject property with optional fields
@given(
    common_name=st.one_of(st.none(), st.text(min_size=1, max_size=64)),
    country=st.one_of(st.none(), st.text(min_size=2, max_size=2)),
    organization=st.one_of(st.none(), st.text(min_size=1, max_size=64))
)
def test_subject_optional_fields(common_name, country, organization):
    """Subject should handle optional fields correctly"""
    kwargs = {}
    if common_name is not None:
        kwargs["CommonName"] = common_name
    if country is not None:
        kwargs["Country"] = country
    if organization is not None:
        kwargs["Organization"] = organization
    
    subject = Subject(**kwargs)
    
    if common_name is not None:
        assert subject.properties.get("CommonName") == common_name
    if country is not None:
        assert subject.properties.get("Country") == country
    if organization is not None:
        assert subject.properties.get("Organization") == organization


# Test 8: KeyUsage with boolean fields
@given(
    crl_sign=st.booleans(),
    digital_signature=st.booleans(),
    key_cert_sign=st.booleans()
)
def test_key_usage_boolean_fields(crl_sign, digital_signature, key_cert_sign):
    """KeyUsage should accept boolean values for its fields"""
    key_usage = KeyUsage(
        CRLSign=crl_sign,
        DigitalSignature=digital_signature,
        KeyCertSign=key_cert_sign
    )
    assert key_usage.properties.get("CRLSign") == crl_sign
    assert key_usage.properties.get("DigitalSignature") == digital_signature
    assert key_usage.properties.get("KeyCertSign") == key_cert_sign


# Test 9: Certificate with required fields
@given(
    ca_arn=st.text(min_size=1).map(lambda x: f"arn:aws:acm-pca:us-east-1:123456789012:certificate-authority/{x}"),
    csr=st.text(min_size=1),
    signing_algo=st.sampled_from(["SHA256WITHRSA", "SHA384WITHRSA", "SHA512WITHRSA"]),
    validity_type=st.sampled_from(["DAYS", "MONTHS", "YEARS"]),
    validity_value=st.floats(min_value=1, max_value=1000, allow_nan=False)
)
def test_certificate_required_fields(ca_arn, csr, signing_algo, validity_type, validity_value):
    """Certificate should accept all required fields"""
    validity = Validity(Type=validity_type, Value=validity_value)
    cert = Certificate(
        title="TestCert",
        CertificateAuthorityArn=ca_arn,
        CertificateSigningRequest=csr,
        SigningAlgorithm=signing_algo,
        Validity=validity
    )
    assert cert.properties["CertificateAuthorityArn"] == ca_arn
    assert cert.properties["CertificateSigningRequest"] == csr
    assert cert.properties["SigningAlgorithm"] == signing_algo
    assert cert.properties["Validity"] == validity


# Test 10: CertificateAuthority with all required fields
@given(
    key_algo=st.sampled_from(["RSA_2048", "RSA_4096", "EC_prime256v1", "EC_secp384r1"]),
    signing_algo=st.sampled_from(["SHA256WITHRSA", "SHA256WITHECDSA"]),
    ca_type=st.sampled_from(["ROOT", "SUBORDINATE"]),
    common_name=st.text(min_size=1, max_size=64)
)
def test_certificate_authority_required_fields(key_algo, signing_algo, ca_type, common_name):
    """CertificateAuthority should accept all required fields"""
    subject = Subject(CommonName=common_name)
    ca = CertificateAuthority(
        title="TestCA",
        KeyAlgorithm=key_algo,
        SigningAlgorithm=signing_algo,
        Type=ca_type,
        Subject=subject
    )
    assert ca.properties["KeyAlgorithm"] == key_algo
    assert ca.properties["SigningAlgorithm"] == signing_algo
    assert ca.properties["Type"] == ca_type
    assert ca.properties["Subject"] == subject


# Test 11: Metamorphic property - validators are idempotent
@given(st.sampled_from(["ABSOLUTE", "DAYS", "END_DATE", "MONTHS", "YEARS"]))
def test_validity_type_idempotent(validity_type):
    """Applying validator twice should give same result as once"""
    once = validate_validity_type(validity_type)
    twice = validate_validity_type(validate_validity_type(validity_type))
    assert once == twice


# Test 12: ExtendedKeyUsage with optional object identifier
@given(
    usage_type=st.one_of(st.none(), st.text(min_size=1)),
    object_id=st.one_of(st.none(), st.text(min_size=1))
)
def test_extended_key_usage_optional_fields(usage_type, object_id):
    """ExtendedKeyUsage should handle optional fields correctly"""
    kwargs = {}
    if usage_type is not None:
        kwargs["ExtendedKeyUsageType"] = usage_type
    if object_id is not None:
        kwargs["ExtendedKeyUsageObjectIdentifier"] = object_id
    
    eku = ExtendedKeyUsage(**kwargs)
    
    if usage_type is not None:
        assert eku.properties.get("ExtendedKeyUsageType") == usage_type
    if object_id is not None:
        assert eku.properties.get("ExtendedKeyUsageObjectIdentifier") == object_id


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])