from hypothesis import given, strategies as st, settings, assume, HealthCheck
import cryptography.x509
from cryptography.x509.oid import NameOID


@given(st.just(""))
def test_empty_value_name_attribute(value):
    attr = cryptography.x509.NameAttribute(NameOID.COMMON_NAME, value)
    name = cryptography.x509.Name([attr])
    
    rfc_string = name.rfc4514_string()
    
    parsed_name = cryptography.x509.Name.from_rfc4514_string(rfc_string)
    
    parsed_attrs = list(parsed_name)
    original_attrs = list(name)
    
    assert len(parsed_attrs) == len(original_attrs)
    assert parsed_attrs[0].value == original_attrs[0].value


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])