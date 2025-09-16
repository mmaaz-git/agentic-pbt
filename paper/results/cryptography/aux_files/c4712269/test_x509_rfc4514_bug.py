from hypothesis import given, strategies as st, settings, assume
import cryptography.x509
from cryptography.x509.oid import NameOID
import string


@st.composite
def rfc4514_special_chars(draw):
    special = ['\\', ',', '+', '"', '<', '>', ';', '#', '=', ' ']
    chars = string.ascii_letters + string.digits + ''.join(special)
    text = draw(st.text(alphabet=chars, min_size=1, max_size=50))
    
    assume('=' in text)
    assume(not text.startswith('='))
    assume(not text.endswith('='))
    assume(text.count('=') >= 1)
    
    return text


@given(rfc4514_special_chars())
@settings(max_examples=200)
def test_rfc4514_parsing_with_special_chars(text):
    try:
        name = cryptography.x509.Name.from_rfc4514_string(text)
        
        rfc_string = name.rfc4514_string()
        
        parsed_again = cryptography.x509.Name.from_rfc4514_string(rfc_string)
        
        assert name == parsed_again
        
    except Exception:
        pass


@given(st.text(alphabet=string.ascii_letters + string.digits + ' ', min_size=1, max_size=50))
def test_name_attribute_with_trailing_spaces(value):
    assume(value != value.strip())
    assume(value.strip() != '')
    
    attr = cryptography.x509.NameAttribute(NameOID.COMMON_NAME, value)
    name = cryptography.x509.Name([attr])
    
    rfc_string = name.rfc4514_string()
    
    parsed_name = cryptography.x509.Name.from_rfc4514_string(rfc_string)
    
    assert name == parsed_name


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])