import django
from django.conf import settings
settings.configure(
    DEBUG=True, 
    SECRET_KEY='test-secret-key',
    MIDDLEWARE=[],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
)
django.setup()

import django.middleware.csrf as csrf


def test_unmask_assertions():
    """Test that _unmask_cipher_token doesn't validate its input properly."""
    
    # The function _unmask_cipher_token doesn't validate token length
    # It should only accept tokens of length CSRF_TOKEN_LENGTH (64)
    # But it processes any input without validation
    
    print("Testing _unmask_cipher_token with invalid inputs:")
    
    # Empty token
    result = csrf._unmask_cipher_token('')
    print(f"Empty token -> result: '{result}', length: {len(result)}")
    assert len(result) == 0  # Should be 32!
    
    # Token too short
    result = csrf._unmask_cipher_token('abc')
    print(f"Token 'abc' -> result: '{result}', length: {len(result)}")
    assert len(result) == 0  # Should be 32!
    
    # Token of length 32 (should be 64)
    token_32 = 'a' * 32
    result = csrf._unmask_cipher_token(token_32)
    print(f"Token of length 32 -> result: '{result}', length: {len(result)}")
    assert len(result) == 0  # Should be 32!
    
    # The function assumes first half is mask, second half is cipher
    # For a 64-char token: first 32 chars are mask, last 32 are cipher
    # But it doesn't validate this assumption
    
    print("\n_unmask_cipher_token implementation issue:")
    print("- It assumes token[:32] is the mask")
    print("- It assumes token[32:] is the cipher")
    print("- But doesn't validate token length is 64")
    print("- Returns wrong-length results for invalid inputs")
    
    print("\nThis violates the contract that unmasked tokens are CSRF_SECRET_LENGTH")
    
    # Show that _does_token_match relies on this contract
    secret = csrf._get_new_csrf_string()
    print(f"\nTesting _does_token_match with secret: {secret}")
    
    try:
        # This will fail the assertion in _does_token_match
        csrf._does_token_match('', secret)
        print("ERROR: Should have raised AssertionError")
    except AssertionError:
        print("AssertionError raised as expected in _does_token_match")
    
    print("\nThe issue: _unmask_cipher_token should validate its input")
    print("Current behavior: Silently returns wrong-length results")
    print("Expected behavior: Should raise an exception for invalid tokens")


def test_token_format_edge_cases():
    """Test edge cases in token format validation."""
    
    print("\nTesting _check_token_format edge cases:")
    
    # Valid lengths are 32 and 64
    for length in [0, 1, 31, 32, 33, 63, 64, 65, 100]:
        token = 'a' * length
        try:
            csrf._check_token_format(token)
            print(f"Length {length}: PASSED validation")
        except csrf.InvalidTokenFormat as e:
            print(f"Length {length}: FAILED validation ({e.reason})")
    
    print("\n_check_token_format correctly validates length")
    print("But _unmask_cipher_token doesn't use this validation")


if __name__ == "__main__":
    test_unmask_assertions()
    test_token_format_edge_cases()