"""Property-based test that reveals the round-trip bug in concatenate/split"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/djangorestframework-api-key_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st


@given(
    left=st.text(min_size=1),
    right=st.text(min_size=1)
)
def test_concatenate_split_round_trip_property(left, right):
    """
    Test that split(concatenate(left, right)) == (left, right)
    
    This is a fundamental round-trip property that should hold for
    any concatenation/splitting function pair.
    """
    from rest_framework_api_key.crypto import concatenate, split
    
    # Concatenate the two parts
    concatenated = concatenate(left, right)
    
    # Split them back
    result_left, result_right = split(concatenated)
    
    # The round-trip property: we should get back what we put in
    assert result_left == left, f"Left part mismatch: expected {repr(left)}, got {repr(result_left)}"
    assert result_right == right, f"Right part mismatch: expected {repr(right)}, got {repr(result_right)}"