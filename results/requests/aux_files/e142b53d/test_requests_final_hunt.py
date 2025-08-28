"""Final comprehensive bug hunt for requests library."""

import string
import json
from hypothesis import given, strategies as st, assume, settings, example
from requests import utils
from requests.structures import CaseInsensitiveDict


# Test unquote_unreserved with complex percent sequences
@given(st.text())
@example("%41%42%43")  # Should become "ABC" 
@example("%41%4")      # Incomplete sequence
@example("%41%")       # Trailing %
@example("%%41")       # Double %
@example("%41%41%41")  # Multiple valid sequences
@settings(max_examples=2000)
def test_unquote_unreserved_edge_cases(text):
    """Test unquote_unreserved with edge case percent encoding."""
    try:
        result = utils.unquote_unreserved(text)
        
        # Test that valid unreserved percent-encoded chars are decoded
        if "%41" in text:  # %41 = 'A' which is unreserved
            # After unquoting, %41 should become A
            assert "%41" not in result or "A" in result
            
        # Test idempotence - applying twice should equal applying once
        result2 = utils.unquote_unreserved(result)
        assert result == result2
        
    except Exception as e:
        # Should only raise InvalidURL for truly invalid sequences
        assert "InvalidURL" in str(type(e).__name__)


# Test requote_uri double encoding issues
@given(st.text(alphabet=string.ascii_letters + string.digits + "%"))
@example("%2520")  # Double-encoded space
@example("%25")    # Encoded percent
@example("%%20")   # Invalid percent sequence
@settings(max_examples=1000) 
def test_requote_uri_double_encoding(uri):
    """Test requote_uri handling of already encoded URIs."""
    try:
        result = utils.requote_uri(uri)
        # Should be idempotent
        result2 = utils.requote_uri(result)
        assert result == result2
        
        # Shouldn't double-encode valid sequences
        if "%20" in uri and "%%" not in uri:
            # Valid encoding should be preserved
            assert "%20" in result or " " in result
            
    except:
        pass


# Test CaseInsensitiveDict with Unicode case folding
@given(st.text(min_size=1, max_size=20))
@example("ß")  # German sharp s
@example("İ")  # Turkish capital I with dot
@settings(max_examples=1000)
def test_case_insensitive_dict_unicode(key):
    """Test CaseInsensitiveDict with Unicode case variations."""
    cid = CaseInsensitiveDict()
    cid[key] = "value1"
    
    # Should handle case-insensitive lookup
    assert cid.get(key.lower()) == "value1"
    assert cid.get(key.upper()) == "value1"
    
    # Update with different case
    cid[key.upper()] = "value2"
    assert cid[key.lower()] == "value2"
    
    # Should only have one key
    assert len(cid) == 1


# Test cookie jar with domain edge cases
@given(
    st.text(min_size=1, alphabet=string.ascii_letters + string.digits + ".-_"),
    st.text()
)
@settings(max_examples=1000)
def test_cookie_jar_special_names(name, value):
    """Test cookie jar with special cookie names."""
    # Some cookie names might be reserved or special
    cookie_dict = {name: value}
    
    try:
        jar = utils.cookiejar_from_dict(cookie_dict)
        result = utils.dict_from_cookiejar(jar)
        
        # Round-trip should preserve the cookie
        assert result == cookie_dict
        
    except Exception as e:
        # Check if it's a known limitation
        print(f"Failed for name='{name}', value='{value}': {e}")
        raise


# Test guess_json_utf with BOM and mixed encodings
@given(st.binary(min_size=0, max_size=20))
@example(b'\xff\xfe\x00\x00')  # UTF-32LE BOM
@example(b'\x00\x00\xfe\xff')  # UTF-32BE BOM  
@example(b'\xff\xfe')           # UTF-16LE BOM
@example(b'\xfe\xff')           # UTF-16BE BOM
@example(b'\xef\xbb\xbf')       # UTF-8 BOM
@settings(max_examples=1000)
def test_guess_json_utf_bom_handling(data):
    """Test guess_json_utf with various BOMs."""
    result = utils.guess_json_utf(data)
    
    # Known BOMs should be detected
    if data.startswith(b'\xff\xfe\x00\x00'):
        assert result == "utf-32"
    elif data.startswith(b'\x00\x00\xfe\xff'):
        assert result == "utf-32"
    elif data.startswith(b'\xef\xbb\xbf'):
        assert result == "utf-8-sig"
    elif data.startswith(b'\xff\xfe') and len(data) >= 2:
        assert result == "utf-16"
    elif data.startswith(b'\xfe\xff'):
        assert result == "utf-16"


# Test from_key_val_list with edge cases
@given(st.one_of(
    st.none(),
    st.lists(st.tuples(st.text(), st.text())),
    st.lists(st.lists(st.text(), min_size=2, max_size=2))
))
@settings(max_examples=1000)
def test_from_key_val_list_edge_cases(value):
    """Test from_key_val_list with various input types."""
    if hasattr(utils, 'from_key_val_list'):
        result = utils.from_key_val_list(value)
        
        if value is None:
            assert result is None
        else:
            assert isinstance(result, dict)
            
            # Test round-trip if possible
            if hasattr(utils, 'to_key_val_list'):
                back = utils.to_key_val_list(result)
                assert isinstance(back, list)