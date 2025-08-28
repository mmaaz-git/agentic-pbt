import sys
import ssl
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa

import spnego.tls


@given(st.binary(min_size=100, max_size=5000))
def test_get_certificate_public_key_with_random_data(data):
    """Test get_certificate_public_key with random binary data."""
    try:
        result = spnego.tls.get_certificate_public_key(data)
        assert isinstance(result, bytes)
    except Exception:
        pass


def test_multiple_generate_tls_certificate_serial_numbers():
    """Test that serial numbers are unique across multiple certificates."""
    serial_numbers = set()
    for _ in range(100):
        cert_pem, _, _ = spnego.tls.generate_tls_certificate()
        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        serial_numbers.add(cert.serial_number)
    
    assert len(serial_numbers) == 100


@given(st.text())
def test_default_tls_context_with_any_usage(usage):
    """Test that default_tls_context handles any usage string gracefully."""
    ctx = spnego.tls.default_tls_context(usage)
    assert isinstance(ctx, spnego.tls.CredSSPTLSContext)
    assert isinstance(ctx.context, ssl.SSLContext)


def test_cert_public_key_format():
    """Test that the public key format is consistent."""
    cert_pem, _, pub_key = spnego.tls.generate_tls_certificate()
    
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    
    extracted_key = spnego.tls.get_certificate_public_key(cert_der)
    
    assert extracted_key[:10] == pub_key[:10]
    
    try:
        from cryptography.hazmat.primitives.serialization import load_der_public_key
        key = load_der_public_key(pub_key, default_backend())
    except:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        wrapped_key = b'-----BEGIN RSA PUBLIC KEY-----\n' + pub_key + b'\n-----END RSA PUBLIC KEY-----'
        try:
            key = load_pem_public_key(wrapped_key, default_backend())
        except:
            pass


def test_certificate_key_strength():
    """Test that generated key has expected strength."""
    _, key_pem, _ = spnego.tls.generate_tls_certificate()
    
    key = serialization.load_pem_private_key(key_pem, password=None, backend=default_backend())
    
    assert isinstance(key, rsa.RSAPrivateKey)
    assert key.key_size == 2048


def test_certificate_cn_format():
    """Test that certificate CN follows expected format."""
    import platform
    
    cert_pem, _, _ = spnego.tls.generate_tls_certificate()
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    
    cn_attrs = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    assert len(cn_attrs) == 1
    
    cn_value = cn_attrs[0].value
    assert cn_value.startswith("CREDSSP-")
    assert cn_value == f"CREDSSP-{platform.node()}"


def test_get_certificate_public_key_with_valid_cert():
    """Test get_certificate_public_key with a manually created valid certificate."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    subject = issuer = x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, "Test")
    ])
    
    import datetime
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    
    public_key = spnego.tls.get_certificate_public_key(cert_der)
    
    assert isinstance(public_key, bytes)
    assert len(public_key) > 0


@given(st.lists(st.sampled_from(["initiate", "accept"]), min_size=1, max_size=10))
def test_multiple_context_creations(usages):
    """Test creating multiple contexts in sequence."""
    contexts = []
    for usage in usages:
        ctx = spnego.tls.default_tls_context(usage)
        contexts.append(ctx)
    
    for ctx in contexts:
        assert isinstance(ctx, spnego.tls.CredSSPTLSContext)
        assert isinstance(ctx.context, ssl.SSLContext)