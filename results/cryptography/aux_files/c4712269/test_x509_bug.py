from hypothesis import given, strategies as st, settings
import cryptography.x509
from cryptography.x509.oid import NameOID


@given(st.text(min_size=0, max_size=0))
def test_empty_rfc4514_string_parsing(text):
    assert text == ""
    name = cryptography.x509.Name.from_rfc4514_string(text)
    
    attrs = list(name)
    assert len(attrs) == 0
    
    rfc_string = name.rfc4514_string()
    
    assert rfc_string != text


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])