#!/usr/bin/env python3
"""Deep property-based tests for troposphere.acmpca module"""

import sys
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the site-packages to path to import troposphere
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.acmpca import (
    Validity, Certificate, CertificateAuthority,
    Subject, CustomAttribute, KeyUsage, GeneralName,
    ExtendedKeyUsage, Extensions, ApiPassthrough,
    Permission, CertificateAuthorityActivation
)
from troposphere.validators.acmpca import (
    validate_validity_type,
    validate_signing_algorithm,
    validate_key_algorithm,
    validate_certificateauthority_type
)

# Test 1: Validator string manipulation - uppercase/lowercase mixing
@given(st.sampled_from(["DAYS", "MONTHS", "YEARS"]))
def test_validator_mixed_case_metamorphic(valid_type):
    """Validators should consistently handle mixed case transformations"""
    # Property: validator(x.lower()) should always fail if validator(x) succeeds
    # (since validators are case-sensitive)
    assert validate_validity_type(valid_type) == valid_type
    
    mixed_case = ""
    for i, char in enumerate(valid_type):
        if i % 2 == 0:
            mixed_case += char.lower()
        else:
            mixed_case += char
    
    if mixed_case != valid_type:
        with pytest.raises(ValueError):
            validate_validity_type(mixed_case)


# Test 2: Cross-validator consistency
def test_signing_algorithm_key_algorithm_consistency():
    """RSA signing algorithms should be compatible with RSA key algorithms"""
    rsa_signing = ["SHA256WITHRSA", "SHA384WITHRSA", "SHA512WITHRSA"]
    ec_signing = ["SHA256WITHECDSA", "SHA384WITHECDSA", "SHA512WITHECDSA"]
    rsa_keys = ["RSA_2048", "RSA_4096"]
    ec_keys = ["EC_prime256v1", "EC_secp384r1"]
    
    # These should all validate successfully
    for algo in rsa_signing:
        assert validate_signing_algorithm(algo) == algo
    for algo in ec_signing:
        assert validate_signing_algorithm(algo) == algo
    for key in rsa_keys:
        assert validate_key_algorithm(key) == key
    for key in ec_keys:
        assert validate_key_algorithm(key) == key


# Test 3: Permission with list of actions
@given(
    actions=st.lists(st.sampled_from([
        "IssueCertificate",
        "GetCertificate",
        "ListPermissions"
    ]), min_size=1, max_size=3, unique=True),
    ca_arn=st.text(min_size=1).map(lambda x: f"arn:aws:acm-pca:us-east-1:123456789012:certificate-authority/{x}"),
    principal=st.text(min_size=1),
    source_account=st.one_of(st.none(), st.text(min_size=12, max_size=12, alphabet="0123456789"))
)
def test_permission_properties(actions, ca_arn, principal, source_account):
    """Permission should handle action lists and optional source account"""
    kwargs = {
        "Actions": actions,
        "CertificateAuthorityArn": ca_arn,
        "Principal": principal
    }
    if source_account is not None:
        kwargs["SourceAccount"] = source_account
    
    perm = Permission(title="TestPermission", **kwargs)
    assert perm.properties["Actions"] == actions
    assert perm.properties["CertificateAuthorityArn"] == ca_arn
    assert perm.properties["Principal"] == principal
    if source_account is not None:
        assert perm.properties.get("SourceAccount") == source_account


# Test 4: CertificateAuthorityActivation properties
@given(
    cert=st.text(min_size=1),
    ca_arn=st.text(min_size=1).map(lambda x: f"arn:aws:acm-pca:us-east-1:123456789012:certificate-authority/{x}"),
    cert_chain=st.one_of(st.none(), st.text(min_size=1)),
    status=st.one_of(st.none(), st.sampled_from(["ACTIVE", "DISABLED"]))
)
def test_certificate_authority_activation(cert, ca_arn, cert_chain, status):
    """CertificateAuthorityActivation should handle optional fields"""
    kwargs = {
        "Certificate": cert,
        "CertificateAuthorityArn": ca_arn
    }
    if cert_chain is not None:
        kwargs["CertificateChain"] = cert_chain
    if status is not None:
        kwargs["Status"] = status
    
    activation = CertificateAuthorityActivation(title="TestActivation", **kwargs)
    assert activation.properties["Certificate"] == cert
    assert activation.properties["CertificateAuthorityArn"] == ca_arn
    if cert_chain is not None:
        assert activation.properties.get("CertificateChain") == cert_chain
    if status is not None:
        assert activation.properties.get("Status") == status


# Test 5: Validity with extreme values
@given(
    validity_type=st.sampled_from(["DAYS", "MONTHS", "YEARS"]),
    value=st.one_of(
        st.just(0.0),
        st.just(-0.0),
        st.floats(min_value=1e-10, max_value=1e-5),  # Very small positive
        st.floats(min_value=1e10, max_value=1e15),   # Very large
    )
)
def test_validity_extreme_values(validity_type, value):
    """Validity should handle extreme float values"""
    validity = Validity(Type=validity_type, Value=value)
    assert validity.properties["Type"] == validity_type
    assert validity.properties["Value"] == value


# Test 6: Certificate with both Validity and ValidityNotBefore
@given(
    ca_arn=st.text(min_size=1).map(lambda x: f"arn:aws:acm-pca:us-east-1:123456789012:certificate-authority/{x}"),
    csr=st.text(min_size=1),
    signing_algo=st.sampled_from(["SHA256WITHRSA", "SHA384WITHRSA"]),
    validity_type=st.sampled_from(["DAYS", "MONTHS"]),
    validity_value=st.floats(min_value=1, max_value=100),
    validity_not_before_type=st.sampled_from(["ABSOLUTE", "DAYS"]),
    validity_not_before_value=st.floats(min_value=1, max_value=30)
)
def test_certificate_dual_validity(ca_arn, csr, signing_algo, validity_type, 
                                  validity_value, validity_not_before_type, 
                                  validity_not_before_value):
    """Certificate should handle both Validity and ValidityNotBefore"""
    validity = Validity(Type=validity_type, Value=validity_value)
    validity_not_before = Validity(Type=validity_not_before_type, Value=validity_not_before_value)
    
    cert = Certificate(
        title="TestCert",
        CertificateAuthorityArn=ca_arn,
        CertificateSigningRequest=csr,
        SigningAlgorithm=signing_algo,
        Validity=validity,
        ValidityNotBefore=validity_not_before
    )
    
    assert cert.properties["Validity"] == validity
    assert cert.properties["ValidityNotBefore"] == validity_not_before


# Test 7: ApiPassthrough with nested structures
@given(
    common_name=st.text(min_size=1, max_size=64),
    country=st.text(min_size=2, max_size=2, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    dns_names=st.lists(st.text(min_size=1, max_size=253), min_size=0, max_size=3)
)
def test_api_passthrough_nested(common_name, country, dns_names):
    """ApiPassthrough should handle nested Subject and Extensions"""
    subject = Subject(CommonName=common_name, Country=country)
    
    if dns_names:
        general_names = [GeneralName(DnsName=dns) for dns in dns_names]
        extensions = Extensions(SubjectAlternativeNames=general_names)
        api_pass = ApiPassthrough(Subject=subject, Extensions=extensions)
        assert api_pass.properties["Extensions"] == extensions
    else:
        api_pass = ApiPassthrough(Subject=subject)
    
    assert api_pass.properties["Subject"] == subject


# Test 8: Metamorphic property - creating same object twice should give same properties
@given(
    key_algo=st.sampled_from(["RSA_2048", "EC_prime256v1"]),
    signing_algo=st.sampled_from(["SHA256WITHRSA", "SHA256WITHECDSA"]),
    ca_type=st.sampled_from(["ROOT", "SUBORDINATE"]),
    common_name=st.text(min_size=1, max_size=64)
)
def test_certificate_authority_deterministic(key_algo, signing_algo, ca_type, common_name):
    """Creating the same CertificateAuthority twice should yield identical properties"""
    subject1 = Subject(CommonName=common_name)
    subject2 = Subject(CommonName=common_name)
    
    ca1 = CertificateAuthority(
        title="TestCA",
        KeyAlgorithm=key_algo,
        SigningAlgorithm=signing_algo,
        Type=ca_type,
        Subject=subject1
    )
    
    ca2 = CertificateAuthority(
        title="TestCA",
        KeyAlgorithm=key_algo,
        SigningAlgorithm=signing_algo,
        Type=ca_type,
        Subject=subject2
    )
    
    # Properties should be the same (except for the Subject object identity)
    assert ca1.properties["KeyAlgorithm"] == ca2.properties["KeyAlgorithm"]
    assert ca1.properties["SigningAlgorithm"] == ca2.properties["SigningAlgorithm"]
    assert ca1.properties["Type"] == ca2.properties["Type"]
    # Subject properties should match even if objects differ
    assert ca1.properties["Subject"].properties == ca2.properties["Subject"].properties


# Test 9: Title validation
@given(st.text())
def test_title_validation(title):
    """Objects should validate their titles according to CloudFormation rules"""
    try:
        ca = CertificateAuthority(
            title=title,
            KeyAlgorithm="RSA_2048",
            SigningAlgorithm="SHA256WITHRSA",
            Type="ROOT",
            Subject=Subject(CommonName="test")
        )
        # If we get here, the title was valid
        # CloudFormation resource names must be alphanumeric
        assert title is None or all(c.isalnum() for c in title)
    except ValueError as e:
        # Title validation failed - should contain specific error message
        if title is not None:
            assert not all(c.isalnum() for c in title) or len(title) == 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])