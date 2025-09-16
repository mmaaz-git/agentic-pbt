#!/usr/bin/env python3
"""Edge case tests for praw.models to find potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings, example
import pytest

from praw.models.util import BoundedSet, ExponentialCounter, permissions_string
from praw.models.reddit.comment import Comment
from praw.exceptions import InvalidURL


# Test URL parsing edge cases more thoroughly
@example(comment_id="def456")  
@example(comment_id="")
@example(comment_id=" ")
@example(comment_id="\n")
@example(comment_id="\t")
@given(
    comment_id=st.text(min_size=0, max_size=20).filter(lambda x: "/" not in x)
)
def test_comment_url_with_trailing_slash(comment_id):
    """Test Comment.id_from_url with trailing slashes and whitespace."""
    base_url = "https://www.reddit.com/r/test/comments/abc123/title/"
    
    # Test with trailing slash
    url_with_slash = base_url + comment_id + "/"
    
    if comment_id.strip():  # Non-empty after stripping
        try:
            result = Comment.id_from_url(url_with_slash)
            # Should extract the ID without the trailing slash
            assert result == comment_id or result == comment_id + "/"
        except InvalidURL:
            # This might be expected for some inputs
            pass


# Test permissions_string with empty known_permissions
@given(
    permissions=st.one_of(
        st.none(),
        st.lists(st.text(min_size=1, max_size=5), min_size=0, max_size=5)
    )
)
def test_permissions_string_empty_known_set(permissions):
    """Test permissions_string when known_permissions is empty."""
    result = permissions_string(known_permissions=set(), permissions=permissions)
    
    if permissions is None:
        assert result == "+all"
    else:
        # With empty known permissions, should still generate a result
        assert result.startswith("-all")
        # Any provided permissions should be added
        for perm in permissions:
            assert f"+{perm}" in result


# Test permissions_string with duplicate permissions
@given(
    known_perms=st.sets(st.text(min_size=1, max_size=5, alphabet='abcde'), min_size=1, max_size=5)
)
def test_permissions_string_duplicate_permissions(known_perms):
    """Test permissions_string with duplicate permissions in the list."""
    # Create a list with duplicates
    perm_list = list(known_perms)
    if perm_list:
        duplicated = perm_list + perm_list  # Double the list
        
        result = permissions_string(known_permissions=known_perms, permissions=duplicated)
        
        # Should handle duplicates correctly
        assert result.startswith("-all")
        
        # Each permission should appear only once in result
        for perm in perm_list:
            assert result.count(f"+{perm}") == 1


# Test ExponentialCounter with float max_counter
@given(max_counter=st.floats(min_value=0.1, max_value=1000.0))
def test_exponential_counter_float_max(max_counter):
    """Test ExponentialCounter with float max_counter values."""
    counter = ExponentialCounter(max_counter)
    
    for _ in range(20):
        value = counter.counter()
        max_with_jitter = max_counter * 1.03125
        assert value <= max_with_jitter


# Test BoundedSet edge case with max_items=0 
def test_bounded_set_zero_max_items():
    """Test BoundedSet with max_items=0."""
    # This is an edge case - what happens with 0 max items?
    bounded_set = BoundedSet(0)
    
    # Try adding items
    for i in range(10):
        bounded_set.add(i)
        # With max_items=0, what's the expected behavior?
        # The implementation will keep 1 item due to how popitem works
        assert len(bounded_set._set) <= 1


# Test BoundedSet with negative max_items
@given(max_items=st.integers(min_value=-100, max_value=-1))
def test_bounded_set_negative_max_items(max_items):
    """Test BoundedSet with negative max_items."""
    bounded_set = BoundedSet(max_items)
    
    # Add items and see what happens
    for i in range(10):
        bounded_set.add(i)
        # With negative max_items, the behavior is undefined
        # But it shouldn't crash
        assert isinstance(bounded_set._set, dict)


# Test Comment.id_from_url with malicious inputs
@example(prefix="https://", domain="www.reddit.com", path_parts=["../..", "comments", "test", "a", "b", "c"])
@example(prefix="https://", domain="www.reddit.com", path_parts=["r", "test", "comments", "../../../etc/passwd"])
@example(prefix="javascript:", domain="alert('xss')", path_parts=["comments", "a", "b", "c", "d"])
@given(
    prefix=st.sampled_from(["http://", "https://", "ftp://", "javascript:", ""]),
    domain=st.sampled_from(["reddit.com", "www.reddit.com", "old.reddit.com", "np.reddit.com", "malicious.com"]),
    path_parts=st.lists(st.text(min_size=0, max_size=20), min_size=0, max_size=10)
)
def test_comment_url_security(prefix, domain, path_parts):
    """Test Comment.id_from_url doesn't have security issues with malicious URLs."""
    url = prefix + domain + "/" + "/".join(path_parts)
    
    try:
        result = Comment.id_from_url(url)
        # If successful, verify it extracted something reasonable
        assert isinstance(result, str)
        assert len(result) > 0
        # The result shouldn't contain path traversal attempts
        assert ".." not in result
        assert "/" not in result
    except (InvalidURL, ValueError, AttributeError) as e:
        # These exceptions are expected for invalid URLs
        pass


# Test permissions_string with special characters
@given(
    known_perms=st.sets(
        st.text(min_size=1, max_size=10).filter(lambda x: x and not x.startswith(('+', '-'))),
        min_size=1,
        max_size=5
    ),
    special_perms=st.lists(
        st.sampled_from(["+all", "-all", "all", "+", "-", "++test", "--test"]),
        min_size=0,
        max_size=5
    )
)
def test_permissions_string_special_values(known_perms, special_perms):
    """Test permissions_string with special permission values."""
    try:
        result = permissions_string(known_permissions=known_perms, permissions=special_perms)
        assert isinstance(result, str)
        
        # The result should handle special values
        if special_perms:
            assert result.startswith("-all")
    except Exception as e:
        # Some special values might cause issues
        print(f"Exception with special perms {special_perms}: {e}")
        raise


# Test for integer overflow in ExponentialCounter
def test_exponential_counter_large_iterations():
    """Test ExponentialCounter with many iterations."""
    counter = ExponentialCounter(2**30)  # Large max value
    
    # Call counter many times to test for overflow
    for _ in range(100):
        value = counter.counter()
        assert isinstance(value, (int, float))
        assert value <= 2**30 * 1.03125


# Test BoundedSet._access with items not in set
@given(
    max_size=st.integers(min_value=1, max_value=10),
    items_to_check=st.lists(st.integers(), min_size=1, max_size=20)
)
def test_bounded_set_access_nonexistent(max_size, items_to_check):
    """Test BoundedSet._access with items not in the set."""
    bounded_set = BoundedSet(max_size)
    
    # Check items that haven't been added
    for item in items_to_check:
        in_set = item in bounded_set  # This calls _access internally
        assert not in_set  # Should be False since we haven't added anything
        assert len(bounded_set._set) == 0  # Set should remain empty


# Test Comment._url_parts (inherited from RedditBase)
def test_comment_url_parts_method():
    """Test the _url_parts method used by id_from_url."""
    # This tests the internal URL parsing
    test_urls = [
        "https://www.reddit.com/r/test/comments/abc/title/def",
        "http://reddit.com/comments/abc/title/def",
        "https://old.reddit.com/r/test/comments/abc/title/def/",
    ]
    
    for url in test_urls:
        try:
            comment_id = Comment.id_from_url(url)
            assert comment_id == "def"
        except InvalidURL:
            pytest.fail(f"Valid URL pattern failed: {url}")


if __name__ == "__main__":
    print("Running edge case tests for praw.models...")
    
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])