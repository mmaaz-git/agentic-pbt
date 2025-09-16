import django
from django.conf import settings
settings.configure(
    DEBUG=True, 
    SECRET_KEY='test-secret-key',
    MIDDLEWARE=[],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
)
django.setup()

import gzip
from hypothesis import given, strategies as st, assume, settings as hyp_settings
import django.middleware.csrf as csrf
import django.utils.text as text
from django.http import HttpRequest, HttpResponse
from django.middleware.gzip import GZipMiddleware


# Test 1: CSRF mask/unmask round-trip property
@given(st.text(alphabet=csrf.CSRF_ALLOWED_CHARS, min_size=csrf.CSRF_SECRET_LENGTH, max_size=csrf.CSRF_SECRET_LENGTH))
def test_csrf_mask_unmask_round_trip(secret):
    """Test that masking and unmasking a CSRF secret is a round-trip operation."""
    token = csrf._mask_cipher_secret(secret)
    unmasked = csrf._unmask_cipher_token(token)
    assert unmasked == secret, f"Round-trip failed: {secret} -> {token} -> {unmasked}"


# Test 2: CSRF token format validation
@given(st.text())
def test_csrf_token_format_validation(token):
    """Test that _check_token_format correctly validates token format."""
    try:
        csrf._check_token_format(token)
        # If no exception, token should have correct length and characters
        assert len(token) in (csrf.CSRF_TOKEN_LENGTH, csrf.CSRF_SECRET_LENGTH)
        assert all(c in csrf.CSRF_ALLOWED_CHARS for c in token)
    except csrf.InvalidTokenFormat as e:
        # If exception, token should violate format rules
        invalid_length = len(token) not in (csrf.CSRF_TOKEN_LENGTH, csrf.CSRF_SECRET_LENGTH)
        invalid_chars = any(c not in csrf.CSRF_ALLOWED_CHARS for c in token)
        assert invalid_length or invalid_chars


# Test 3: Masked token format property
@given(st.text(alphabet=csrf.CSRF_ALLOWED_CHARS, min_size=csrf.CSRF_SECRET_LENGTH, max_size=csrf.CSRF_SECRET_LENGTH))
def test_masked_token_has_correct_format(secret):
    """Test that masked tokens have the correct format."""
    token = csrf._mask_cipher_secret(secret)
    assert len(token) == csrf.CSRF_TOKEN_LENGTH
    assert all(c in csrf.CSRF_ALLOWED_CHARS for c in token)
    # Should pass format check
    csrf._check_token_format(token)


# Test 4: Unmasking different masks of same secret produces same result
@given(
    st.text(alphabet=csrf.CSRF_ALLOWED_CHARS, min_size=csrf.CSRF_SECRET_LENGTH, max_size=csrf.CSRF_SECRET_LENGTH)
)
def test_multiple_masks_same_secret(secret):
    """Test that different masks of the same secret unmask to the same value."""
    token1 = csrf._mask_cipher_secret(secret)
    token2 = csrf._mask_cipher_secret(secret)
    # Tokens should be different (different masks)
    # But unmask to same secret
    assert csrf._unmask_cipher_token(token1) == secret
    assert csrf._unmask_cipher_token(token2) == secret


# Test 5: GZip compression property
@given(st.binary(min_size=200))  # GZip only compresses content >= 200 bytes
@hyp_settings(max_examples=100)
def test_gzip_compression_size_property(content):
    """Test that GZipMiddleware only applies compression if it reduces size."""
    request = HttpRequest()
    request.META = {'HTTP_ACCEPT_ENCODING': 'gzip'}
    
    response = HttpResponse(content)
    response['Content-Type'] = 'text/html'
    
    middleware = GZipMiddleware(lambda r: None)
    processed = middleware.process_response(request, response)
    
    if 'gzip' in processed.get('Content-Encoding', ''):
        # If gzipped, compressed content should be shorter than original
        assert len(processed.content) < len(content)
    else:
        # If not gzipped, either:
        # 1. Compressed would be longer/equal
        # 2. Other conditions prevented compression
        compressed = text.compress_string(content)
        if len(content) >= 200 and not response.has_header('Content-Encoding'):
            # Compression was attempted but not applied
            assert len(compressed) >= len(content)


# Test 6: Token validation edge cases
@given(st.one_of(
    st.text(alphabet=csrf.CSRF_ALLOWED_CHARS, min_size=0, max_size=200),
    st.text(min_size=0, max_size=200)
))
def test_csrf_token_validation_comprehensive(token):
    """Comprehensive test of CSRF token format validation."""
    is_valid_format = (
        len(token) in (csrf.CSRF_TOKEN_LENGTH, csrf.CSRF_SECRET_LENGTH) and
        all(c in csrf.CSRF_ALLOWED_CHARS for c in token)
    )
    
    try:
        csrf._check_token_format(token)
        assert is_valid_format, f"Token '{token}' passed validation but shouldn't have"
    except csrf.InvalidTokenFormat:
        assert not is_valid_format, f"Token '{token}' failed validation but shouldn't have"


# Test 7: Mask operation properties
@given(
    st.text(alphabet=csrf.CSRF_ALLOWED_CHARS, min_size=csrf.CSRF_SECRET_LENGTH, max_size=csrf.CSRF_SECRET_LENGTH),
    st.text(alphabet=csrf.CSRF_ALLOWED_CHARS, min_size=csrf.CSRF_SECRET_LENGTH, max_size=csrf.CSRF_SECRET_LENGTH)
)
def test_mask_operation_properties(secret1, secret2):
    """Test properties of the masking operation."""
    token1 = csrf._mask_cipher_secret(secret1)
    token2 = csrf._mask_cipher_secret(secret2)
    
    # Different secrets should produce different tokens (with high probability)
    if secret1 != secret2:
        # The tokens contain both mask and cipher, so even with same mask they'd differ
        pass  # Can't guarantee tokens are different due to random masks
    
    # Each token should unmask to its original secret
    assert csrf._unmask_cipher_token(token1) == secret1
    assert csrf._unmask_cipher_token(token2) == secret2


# Test 8: Invalid token unmasking
@given(st.text(min_size=0, max_size=200))
def test_invalid_token_unmasking(token):
    """Test unmasking invalid tokens."""
    if len(token) != csrf.CSRF_TOKEN_LENGTH:
        # Should not be able to unmask invalid length tokens
        try:
            result = csrf._unmask_cipher_token(token)
            # If it doesn't raise an error, it might return wrong result
            # Check if result has correct length at least
            assert len(result) == csrf.CSRF_SECRET_LENGTH
        except (IndexError, ValueError):
            pass  # Expected for invalid tokens
    elif not all(c in csrf.CSRF_ALLOWED_CHARS for c in token):
        # Invalid characters should cause issues
        try:
            result = csrf._unmask_cipher_token(token)
        except (ValueError, IndexError):
            pass  # Expected for invalid characters


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])