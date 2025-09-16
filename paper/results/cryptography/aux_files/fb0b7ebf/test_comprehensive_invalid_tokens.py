"""Comprehensive property test for invalid token handling."""
from hypothesis import given, strategies as st, settings
from cryptography.fernet import Fernet, InvalidToken
import pytest

# Generate various invalid token strings
invalid_token_strategy = st.one_of(
    # Non-ASCII characters
    st.text(min_size=1).filter(lambda x: any(ord(c) > 127 for c in x)),
    # Non-base64 characters
    st.text(alphabet='!@#$%^&*(){}[]<>?', min_size=1),
    # Mixed invalid characters
    st.text(min_size=1).map(lambda x: x + '\x00'),
    # Unicode characters
    st.sampled_from(['😀', '🦄', 'Ā', '•', '\u2022', '\u00ff']),
    # Control characters
    st.text(alphabet=''.join(chr(i) for i in range(32)), min_size=1),
)

@given(invalid_token_strategy)
@settings(max_examples=500)
def test_all_invalid_tokens_raise_InvalidToken(invalid_token):
    """All invalid tokens should raise InvalidToken, never ValueError."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    # Test decrypt
    with pytest.raises(InvalidToken):
        f.decrypt(invalid_token)
    
    # Test decrypt_at_time
    with pytest.raises(InvalidToken):
        f.decrypt_at_time(invalid_token, ttl=100, current_time=1000)
    
    # Test extract_timestamp
    with pytest.raises(InvalidToken):
        f.extract_timestamp(invalid_token)

if __name__ == "__main__":
    test_all_invalid_tokens_raise_InvalidToken()
    print("Test completed!")