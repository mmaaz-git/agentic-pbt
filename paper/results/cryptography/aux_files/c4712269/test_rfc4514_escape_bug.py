from hypothesis import given, strategies as st
import cryptography.x509
from cryptography.x509.oid import NameOID


@given(st.just("#"))
def test_rfc4514_hash_escape_round_trip(char):
    value = f"test{char}test"
    
    attr = cryptography.x509.NameAttribute(NameOID.COMMON_NAME, value)
    name = cryptography.x509.Name([attr])
    
    rfc_string = name.rfc4514_string()
    
    parsed_name = cryptography.x509.Name.from_rfc4514_string(rfc_string)
    
    original_value = list(name)[0].value
    parsed_value = list(parsed_name)[0].value
    
    assert original_value == parsed_value


@given(st.just("="))
def test_rfc4514_equals_escape_round_trip(char):
    value = f"test{char}test"
    
    attr = cryptography.x509.NameAttribute(NameOID.COMMON_NAME, value)
    name = cryptography.x509.Name([attr])
    
    rfc_string = name.rfc4514_string()
    
    parsed_name = cryptography.x509.Name.from_rfc4514_string(rfc_string)
    
    original_value = list(name)[0].value
    parsed_value = list(parsed_name)[0].value
    
    assert original_value == parsed_value


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])