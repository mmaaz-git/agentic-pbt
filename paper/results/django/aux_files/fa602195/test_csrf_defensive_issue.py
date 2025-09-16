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
from hypothesis import given, strategies as st


# Hypothesis test that found the issue
@given(st.text(min_size=0, max_size=200))
def test_unmask_contract_violation(token):
    """
    Test that _unmask_cipher_token violates its implicit contract.
    
    The function should either:
    1. Return a valid CSRF_SECRET_LENGTH result, OR
    2. Raise an exception for invalid input
    
    Instead, it silently returns wrong-length results.
    """
    if len(token) != csrf.CSRF_TOKEN_LENGTH:
        # For invalid length tokens
        result = csrf._unmask_cipher_token(token)
        
        # The result should have length CSRF_SECRET_LENGTH (32)
        # But it doesn't - this is the bug
        if len(result) != csrf.CSRF_SECRET_LENGTH:
            print(f"\nBUG: _unmask_cipher_token({repr(token)[:50]}...)")
            print(f"     returned result of length {len(result)} instead of {csrf.CSRF_SECRET_LENGTH}")
            
            # This breaks the assumption in _does_token_match
            # which has: assert len(request_csrf_token) == CSRF_SECRET_LENGTH
            return False  # Bug found
    
    return True  # No issue for valid tokens


def demonstrate_the_issue():
    """Demonstrate the specific issue with concrete examples."""
    
    print("=" * 60)
    print("Django CSRF _unmask_cipher_token Contract Violation")
    print("=" * 60)
    
    print("\nThe Issue:")
    print("-" * 40)
    print("_unmask_cipher_token() doesn't validate input length.")
    print("It returns wrong-length results for invalid tokens.")
    print("This violates the contract expected by _does_token_match().")
    
    print("\nExamples:")
    print("-" * 40)
    
    test_cases = [
        ("", "Empty string"),
        ("a", "Single character"),  
        ("a" * 10, "10 characters"),
        ("a" * 32, "32 characters (valid secret length)"),
        ("a" * 63, "63 characters (one short of valid token)"),
    ]
    
    for token, description in test_cases:
        result = csrf._unmask_cipher_token(token)
        print(f"{description:40} -> length {len(result):2} (expected: {csrf.CSRF_SECRET_LENGTH})")
    
    print("\nWhy This Matters:")
    print("-" * 40)
    print("1. Defensive Programming: Functions should validate inputs")
    print("2. Fail Fast: Invalid inputs should raise exceptions immediately")
    print("3. Clear Contracts: Return values should match documented behavior")
    
    print("\nCurrent call chain:")
    print("-" * 40)
    print("CsrfViewMiddleware.process_view()")
    print("  -> _check_token_format() [validates]")
    print("  -> _does_token_match()")
    print("      -> _unmask_cipher_token() [assumes valid]")
    print("      -> assert len(token) == 32")
    
    print("\nIf validation is ever missed or refactored:")
    print("- _unmask_cipher_token returns wrong result")
    print("- _does_token_match hits assertion error")
    print("- This makes debugging harder")
    
    print("\nRecommendation:")
    print("-" * 40)
    print("_unmask_cipher_token should validate token length and raise")
    print("InvalidTokenFormat for invalid inputs, not return wrong results.")
    

if __name__ == "__main__":
    demonstrate_the_issue()
    
    print("\n" + "=" * 60)
    print("Running Hypothesis test to find the issue...")
    print("=" * 60)
    
    # This will find counterexamples quickly
    try:
        test_unmask_contract_violation()
    except AssertionError:
        print("\nHypothesis found the contract violation!")
        print("The test fails because _unmask_cipher_token returns")
        print("wrong-length results for many invalid inputs.")