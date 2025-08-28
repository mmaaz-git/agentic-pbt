"""
Comprehensive test demonstrating the empty value data loss bug in urllib.parse
"""
import urllib.parse
from hypothesis import given, strategies as st, assume


@given(st.dictionaries(
    st.text(min_size=1, alphabet=st.characters(blacklist_characters='&=\x00')),
    st.text(alphabet=st.characters(blacklist_characters='&=\x00')),
    min_size=1,
    max_size=10
))
def test_urlencode_parse_qs_loses_empty_values(data):
    """
    Property: urlencode -> parse_qs should preserve all keys
    Bug: Keys with empty string values are lost
    """
    encoded = urllib.parse.urlencode(data)
    decoded = urllib.parse.parse_qs(encoded)  # default keep_blank_values=False
    
    # Count how many keys are lost
    lost_keys = set(data.keys()) - set(decoded.keys())
    
    # All lost keys should have empty values
    for key in lost_keys:
        assert data[key] == ''
    
    # This assertion will fail, demonstrating the bug
    if any(v == '' for v in data.values()):
        assert len(lost_keys) > 0, "Empty values cause data loss"


@given(st.lists(
    st.tuples(
        st.text(min_size=1, alphabet=st.characters(blacklist_characters='&=\x00')),
        st.text(alphabet=st.characters(blacklist_characters='&=\x00'))
    ),
    min_size=1,
    max_size=10
))
def test_urlencode_parse_qsl_loses_empty_values(pairs):
    """
    Property: urlencode -> parse_qsl should preserve all pairs
    Bug: Pairs with empty values are lost
    """
    encoded = urllib.parse.urlencode(pairs)
    decoded = urllib.parse.parse_qsl(encoded)  # default keep_blank_values=False
    
    # Count pairs with empty values
    empty_value_count = sum(1 for _, v in pairs if v == '')
    
    # This will demonstrate the data loss
    assert len(decoded) == len(pairs) - empty_value_count


def test_specific_example():
    """Minimal example demonstrating the bug"""
    # Example 1: Dictionary with empty value
    data = {'username': 'alice', 'password': ''}
    encoded = urllib.parse.urlencode(data)
    decoded = urllib.parse.parse_qs(encoded)
    
    print(f"Original: {data}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")
    print(f"Lost key 'password': {'password' not in decoded}")
    assert 'password' not in decoded  # Bug: password key is lost
    
    # Example 2: With keep_blank_values=True (correct behavior)
    decoded_correct = urllib.parse.parse_qs(encoded, keep_blank_values=True)
    print(f"\nWith keep_blank_values=True: {decoded_correct}")
    assert 'password' in decoded_correct
    assert decoded_correct['password'] == ['']


if __name__ == "__main__":
    # Run the specific example
    test_specific_example()
    
    # Run property tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_urlencode"])