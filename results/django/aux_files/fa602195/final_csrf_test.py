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
from hypothesis import given, strategies as st, assume


@given(st.text(min_size=0, max_size=200))
def test_unmask_returns_correct_length(token):
    """
    Property: _unmask_cipher_token should always return a 32-character result
    for any 64-character input, regardless of content.
    
    Bug: It returns wrong-length results for invalid inputs.
    """
    if len(token) == csrf.CSRF_TOKEN_LENGTH:
        # Valid length token - should work correctly
        result = csrf._unmask_cipher_token(token)
        assert len(result) == csrf.CSRF_SECRET_LENGTH
    else:
        # Invalid length - function doesn't validate!
        result = csrf._unmask_cipher_token(token)
        # This assertion SHOULD pass if the function was defensive
        # But it fails, revealing the bug
        assert len(result) == csrf.CSRF_SECRET_LENGTH, \
            f"_unmask_cipher_token returned {len(result)}-char result for {len(token)}-char input"


def minimal_reproduction():
    """Minimal reproduction of the bug."""
    print("Minimal Bug Reproduction")
    print("=" * 40)
    
    # The bug: _unmask_cipher_token doesn't validate input
    result = csrf._unmask_cipher_token("")
    print(f"csrf._unmask_cipher_token('') returns: {repr(result)}")
    print(f"Length: {len(result)} (should be {csrf.CSRF_SECRET_LENGTH})")
    
    print("\nThis violates the implicit contract that unmasked")
    print("tokens are always CSRF_SECRET_LENGTH characters.")
    
    # Show how this breaks _does_token_match
    print("\nConsequence in _does_token_match:")
    secret = csrf._get_new_csrf_string()
    try:
        csrf._does_token_match("", secret)
    except AssertionError:
        print("AssertionError: assert len(request_csrf_token) == CSRF_SECRET_LENGTH")
        print("                       ^--- fails because unmask returned empty string")


if __name__ == "__main__":
    minimal_reproduction()
    
    print("\n" + "=" * 40)
    print("Running property-based test...")
    print("=" * 40)
    
    # Run the test - it will fail on empty string
    import pytest
    pytest.main([__file__, "-k", "test_unmask_returns_correct_length", "-v"])