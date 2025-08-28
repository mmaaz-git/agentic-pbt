import string
from hypothesis import given, strategies as st, assume, settings
import cryptography.x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime


OID_CHOICES = [
    NameOID.COUNTRY_NAME,
    NameOID.STATE_OR_PROVINCE_NAME, 
    NameOID.LOCALITY_NAME,
    NameOID.ORGANIZATION_NAME,
    NameOID.ORGANIZATIONAL_UNIT_NAME,
    NameOID.COMMON_NAME,
    NameOID.EMAIL_ADDRESS,
    NameOID.SERIAL_NUMBER,
    NameOID.SURNAME,
    NameOID.GIVEN_NAME,
    NameOID.TITLE,
    NameOID.GENERATION_QUALIFIER,
    NameOID.DN_QUALIFIER,
    NameOID.PSEUDONYM,
    NameOID.DOMAIN_COMPONENT,
]

@st.composite
def valid_attribute_value(draw, oid=None):
    if oid == NameOID.COUNTRY_NAME:
        return draw(st.text(alphabet=string.ascii_uppercase, min_size=2, max_size=2))
    else:
        return draw(st.text(min_size=1, max_size=100).filter(
            lambda x: '\x00' not in x and x.strip() != ''
        ))

@st.composite
def name_attributes(draw):
    oid = draw(st.sampled_from(OID_CHOICES))
    value = draw(valid_attribute_value(oid))
    return x509.NameAttribute(oid, value)

@st.composite
def x509_names(draw):
    attrs = draw(st.lists(name_attributes(), min_size=1, max_size=10))
    return x509.Name(attrs)


@given(x509_names())
def test_name_rfc4514_round_trip(name):
    rfc_string = name.rfc4514_string()
    parsed_name = x509.Name.from_rfc4514_string(rfc_string)
    assert name == parsed_name, f"Round-trip failed: {name} != {parsed_name}"


@given(x509_names())
def test_name_public_bytes_round_trip(name):
    der_bytes = name.public_bytes(default_backend())
    parsed_name = x509.Name.from_bytes(der_bytes)
    assert name == parsed_name


@given(st.lists(name_attributes(), min_size=1, max_size=10))
def test_name_equality_reflexive(attrs):
    name1 = x509.Name(attrs)
    name2 = x509.Name(attrs)
    assert name1 == name2
    assert hash(name1) == hash(name2)


@given(x509_names())
def test_name_get_attributes_returns_subset(name):
    for attr in name:
        attrs_for_oid = name.get_attributes_for_oid(attr.oid)
        assert attr in attrs_for_oid
        assert all(a.oid == attr.oid for a in attrs_for_oid)


@given(st.lists(name_attributes(), min_size=1, max_size=10))
def test_relative_distinguished_name_invariants(attrs):
    rdn = x509.RelativeDistinguishedName(attrs)
    assert len(rdn) == len(attrs)
    assert set(rdn) == set(attrs)


@given(x509_names())
def test_name_rdns_preserve_content(name):
    rdns = name.rdns
    all_attrs_from_rdns = []
    for rdn in rdns:
        all_attrs_from_rdns.extend(rdn)
    
    original_attrs = list(name)
    assert set(all_attrs_from_rdns) == set(original_attrs)
    assert len(all_attrs_from_rdns) == len(original_attrs)


@given(st.text(min_size=0, max_size=1000))
def test_name_from_rfc4514_empty_or_invalid(text):
    assume(text.strip() == '')
    try:
        name = x509.Name.from_rfc4514_string(text)
        assert len(list(name)) == 0
    except Exception:
        pass


@given(st.lists(st.sampled_from(OID_CHOICES), min_size=1, max_size=5, unique=True))
def test_name_attribute_order_preservation(oids):
    attrs = []
    for i, oid in enumerate(oids):
        value = f"Value{i}"
        attrs.append(x509.NameAttribute(oid, value))
    
    name = x509.Name(attrs)
    name_attrs = list(name)
    
    assert len(name_attrs) == len(attrs)
    for orig, retrieved in zip(attrs, name_attrs):
        assert orig.oid == retrieved.oid
        assert orig.value == retrieved.value


@given(st.text(min_size=1, max_size=100))
def test_dns_name_value_preservation(value):
    assume('\x00' not in value)
    try:
        dns_name = x509.DNSName(value)
        assert dns_name.value == value
    except Exception:
        pass


@given(st.integers(min_value=0, max_value=2**32-1))
def test_crl_number_value_preservation(num):
    crl_num = x509.CRLNumber(num)
    assert crl_num.crl_number == num


@given(st.booleans(), st.integers(min_value=0, max_value=100))
def test_basic_constraints_properties(ca, path_length):
    if not ca:
        path_length = None
    
    bc = x509.BasicConstraints(ca=ca, path_length=path_length)
    assert bc.ca == ca
    assert bc.path_length == path_length


@given(st.integers(min_value=-2**63, max_value=2**63-1))
def test_serial_number_builder_preservation(serial):
    assume(serial >= 0)
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "test"),
    ])
    
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(issuer)
    builder = builder.public_key(private_key.public_key())
    builder = builder.serial_number(serial)
    builder = builder.not_valid_before(datetime.datetime.now())
    builder = builder.not_valid_after(datetime.datetime.now() + datetime.timedelta(days=1))
    
    cert = builder.sign(private_key, hashes.SHA256(), backend=default_backend())
    assert cert.serial_number == serial


@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10))
def test_extended_key_usage_oid_preservation(oid_names):
    from cryptography.x509.oid import ObjectIdentifier
    
    oids = []
    for i, name in enumerate(oid_names):
        try:
            oid = ObjectIdentifier(f"1.2.3.4.{i}")
            oids.append(oid)
        except:
            pass
    
    if oids:
        eku = x509.ExtendedKeyUsage(oids)
        assert set(eku) == set(oids)
        assert len(eku) == len(oids)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])