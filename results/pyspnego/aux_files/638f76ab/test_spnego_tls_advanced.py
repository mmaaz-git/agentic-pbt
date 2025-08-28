import sys
import ssl
import datetime
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, note
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

import spnego.tls


def test_ssl_options_accumulate():
    """Test that SSL options are ORed, not replaced."""
    ctx = spnego.tls.default_tls_context("initiate")
    
    initial_options = ctx.context.options
    
    expected_flags = ssl.OP_NO_COMPRESSION | 0x00000200 | 0x00000800
    assert (initial_options & expected_flags) == expected_flags
    
    ctx2 = spnego.tls.default_tls_context("accept")
    initial_options2 = ctx2.context.options
    assert (initial_options2 & expected_flags) == expected_flags


def test_cert_signature_algorithm():
    """Test that the certificate uses SHA256 as specified."""
    cert_pem, _, _ = spnego.tls.generate_tls_certificate()
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    
    assert cert.signature_algorithm_oid._name == "sha256WithRSAEncryption"


def test_certificate_public_key_can_verify():
    """Test that the public key can be used to verify signatures."""
    cert_pem, key_pem, pub_key_der = spnego.tls.generate_tls_certificate()
    
    private_key = serialization.load_pem_private_key(
        key_pem, password=None, backend=default_backend()
    )
    
    message = b"Test message"
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    public_key = cert.public_key()
    
    public_key.verify(
        signature,
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )


def test_certificate_dates_ordering():
    """Test that not_valid_before < not_valid_after."""
    for _ in range(10):
        cert_pem, _, _ = spnego.tls.generate_tls_certificate()
        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        
        assert cert.not_valid_before_utc < cert.not_valid_after_utc
        
        now = datetime.datetime.now(datetime.timezone.utc)
        assert cert.not_valid_before_utc <= now
        assert cert.not_valid_after_utc >= now


def test_certificate_immutability():
    """Test that the certificate data is consistent."""
    cert_pem1, key_pem1, pub_key1 = spnego.tls.generate_tls_certificate()
    
    cert1 = x509.load_pem_x509_certificate(cert_pem1, default_backend())
    cert_der1 = cert1.public_bytes(serialization.Encoding.DER)
    
    extracted_pub_key1 = spnego.tls.get_certificate_public_key(cert_der1)
    
    assert extracted_pub_key1 == pub_key1
    
    extracted_pub_key2 = spnego.tls.get_certificate_public_key(cert_der1)
    assert extracted_pub_key1 == extracted_pub_key2


@given(st.data())
def test_tls_context_properties_preserved(data):
    """Test that context properties are preserved across different usage values."""
    usage = data.draw(st.sampled_from(["initiate", "accept"]))
    
    ctx = spnego.tls.default_tls_context(usage)
    
    assert hasattr(ctx.context, 'options')
    assert hasattr(ctx.context, 'verify_mode')
    
    if usage == "initiate":
        assert ctx.context.verify_mode == ssl.CERT_NONE
        assert ctx.context.check_hostname is False


def test_public_key_extraction_consistency():
    """Test that extracting public key multiple times gives same result."""
    cert_pem, _, original_pub_key = spnego.tls.generate_tls_certificate()
    
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    
    extracted_keys = []
    for _ in range(10):
        extracted_key = spnego.tls.get_certificate_public_key(cert_der)
        extracted_keys.append(extracted_key)
    
    assert all(key == original_pub_key for key in extracted_keys)
    assert all(key == extracted_keys[0] for key in extracted_keys)


def test_empty_certificate_handling():
    """Test behavior with empty or minimal data."""
    try:
        result = spnego.tls.get_certificate_public_key(b'')
    except Exception as e:
        assert True
    
    try:
        result = spnego.tls.get_certificate_public_key(b'\x00')
    except Exception as e:
        assert True


def test_default_tls_context_no_side_effects():
    """Test that creating contexts doesn't have side effects."""
    ctx1 = spnego.tls.default_tls_context("initiate")
    original_options1 = ctx1.context.options
    
    ctx2 = spnego.tls.default_tls_context("initiate")
    
    assert ctx1.context.options == original_options1
    
    ctx1.context.options |= 0x10000000
    
    ctx3 = spnego.tls.default_tls_context("initiate")
    assert ctx3.context.options != ctx1.context.options


@given(st.integers(min_value=0, max_value=1000))
@settings(deadline=None)
def test_certificate_serial_number_randomness(seed):
    """Test that serial numbers are properly randomized."""
    import random
    random.seed(seed)
    
    serials = []
    for _ in range(5):
        cert_pem, _, _ = spnego.tls.generate_tls_certificate()
        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        serials.append(cert.serial_number)
    
    assert len(set(serials)) == len(serials)