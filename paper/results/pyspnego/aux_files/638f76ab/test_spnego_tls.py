import datetime
import ssl
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

import spnego.tls


@given(st.sampled_from(["initiate", "accept"]))
def test_default_tls_context_returns_valid_context(usage):
    """Test that default_tls_context always returns a valid CredSSPTLSContext."""
    result = spnego.tls.default_tls_context(usage)
    
    assert isinstance(result, spnego.tls.CredSSPTLSContext)
    assert isinstance(result.context, ssl.SSLContext)
    assert result.public_key is None
    
    if usage == "initiate":
        assert result.context.check_hostname is False
        assert result.context.verify_mode == ssl.CERT_NONE


@given(st.text(min_size=1, max_size=100))
def test_default_tls_context_with_invalid_usage(usage):
    """Test behavior with arbitrary usage values."""
    if usage not in ["initiate", "accept"]:
        result = spnego.tls.default_tls_context(usage)
        assert isinstance(result, spnego.tls.CredSSPTLSContext)
        assert isinstance(result.context, ssl.SSLContext)


def test_generate_tls_certificate_returns_valid_types():
    """Test that generate_tls_certificate returns proper types."""
    cert_pem, key_pem, public_key = spnego.tls.generate_tls_certificate()
    
    assert isinstance(cert_pem, bytes)
    assert isinstance(key_pem, bytes)
    assert isinstance(public_key, bytes)
    
    assert b'-----BEGIN CERTIFICATE-----' in cert_pem
    assert b'-----END CERTIFICATE-----' in cert_pem
    assert b'-----BEGIN RSA PRIVATE KEY-----' in key_pem
    assert b'-----END RSA PRIVATE KEY-----' in key_pem


def test_generate_tls_certificate_validity_period():
    """Test that certificate has correct validity period."""
    cert_pem, _, _ = spnego.tls.generate_tls_certificate()
    
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    
    validity_period = cert.not_valid_after_utc - cert.not_valid_before_utc
    expected_period = datetime.timedelta(days=365)
    
    assert validity_period == expected_period


def test_certificate_round_trip_property():
    """Test round-trip property: generated public key matches extracted public key."""
    cert_pem, _, generated_public_key = spnego.tls.generate_tls_certificate()
    
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    
    extracted_public_key = spnego.tls.get_certificate_public_key(cert_der)
    
    assert extracted_public_key == generated_public_key


@given(st.binary(min_size=1, max_size=10))
def test_get_certificate_public_key_with_invalid_input(data):
    """Test get_certificate_public_key with invalid DER data."""
    try:
        spnego.tls.get_certificate_public_key(data)
    except Exception:
        pass


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=50, deadline=None)
def test_generate_tls_certificate_consistency(n):
    """Test that multiple calls to generate_tls_certificate produce different certificates."""
    certificates = []
    for _ in range(n):
        cert_pem, key_pem, pub_key = spnego.tls.generate_tls_certificate()
        certificates.append((cert_pem, key_pem, pub_key))
    
    for i in range(len(certificates)):
        for j in range(i + 1, len(certificates)):
            assert certificates[i][0] != certificates[j][0]
            assert certificates[i][1] != certificates[j][1]


def test_generate_certificate_self_signed():
    """Test that generated certificate is self-signed."""
    cert_pem, _, _ = spnego.tls.generate_tls_certificate()
    
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    
    assert cert.issuer == cert.subject
    
    cn_attrs = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    assert len(cn_attrs) == 1
    assert cn_attrs[0].value.startswith("CREDSSP-")


@given(st.sampled_from(["initiate", "accept"]))
def test_tls_context_ssl_options(usage):
    """Test that SSL options are correctly set."""
    result = spnego.tls.default_tls_context(usage)
    
    expected_options = ssl.OP_NO_COMPRESSION | 0x00000200 | 0x00000800
    
    assert (result.context.options & expected_options) == expected_options