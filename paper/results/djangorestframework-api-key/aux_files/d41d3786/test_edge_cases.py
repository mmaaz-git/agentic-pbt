import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/djangorestframework-api-key_env/lib/python3.13/site-packages')

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework_api_key',
        ],
        USE_TZ=True,
        SECRET_KEY='test-secret-key',
    )
    django.setup()

from hypothesis import given, strategies as st
from rest_framework_api_key.crypto import concatenate, split


# Test the round-trip property when left contains dots
@given(
    left=st.text(min_size=1, max_size=100),  # Allow dots in left
    right=st.text(min_size=1, max_size=100)
)
def test_concatenate_split_dots_in_left(left, right):
    """Test concatenate/split when left part contains dots"""
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    
    # This might fail if left contains dots!
    # The split function uses partition('.') which splits on first dot
    print(f"Input: left='{left}', right='{right}'")
    print(f"Concatenated: '{concatenated}'")
    print(f"After split: left='{result_left}', right='{result_right}'")
    
    assert result_left == left, f"Left mismatch: expected '{left}', got '{result_left}'"
    assert result_right == right, f"Right mismatch: expected '{right}', got '{result_right}'"


# Test what happens with multiple dots
def test_specific_dot_case():
    """Test specific case with dot in left part"""
    left = "abc.def"
    right = "xyz"
    
    concatenated = concatenate(left, right)
    print(f"Concatenated '{left}' and '{right}': '{concatenated}'")
    
    result_left, result_right = split(concatenated)
    print(f"After split: left='{result_left}', right='{result_right}'")
    
    # Expected: left='abc.def', right='xyz'
    # Actual: left='abc', right='def.xyz' (because split uses partition on first dot)
    assert result_left == left, f"Expected left='{left}', got '{result_left}'"
    assert result_right == right, f"Expected right='{right}', got '{result_right}'"


if __name__ == "__main__":
    print("Testing specific dot case...")
    try:
        test_specific_dot_case()
        print("✓ Specific test passed")
    except AssertionError as e:
        print(f"✗ Specific test failed: {e}")
    
    print("\nTesting with Hypothesis...")
    try:
        test_concatenate_split_dots_in_left()
        print("✓ Hypothesis test passed")
    except Exception as e:
        print(f"✗ Hypothesis test failed: {e}")