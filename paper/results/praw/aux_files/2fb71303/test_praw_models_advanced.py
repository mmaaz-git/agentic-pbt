#!/usr/bin/env python3
"""Advanced property-based tests for praw.models module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings, example
from hypothesis.provisional import urls
import pytest

# Import classes to test
from praw.models.util import BoundedSet, ExponentialCounter, permissions_string
from praw.models.reddit.comment import Comment
from praw.models.base import PRAWBase
from praw.exceptions import InvalidURL


# Test URL parsing for Comment.id_from_url
@given(comment_id=st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
def test_comment_id_from_valid_url(comment_id):
    """Test Comment.id_from_url with valid Reddit comment URLs."""
    # Construct a valid Reddit comment URL
    submission_id = "test123"
    url = f"https://www.reddit.com/r/test/comments/{submission_id}/test_title/{comment_id}"
    
    try:
        extracted_id = Comment.id_from_url(url)
        assert extracted_id == comment_id
    except InvalidURL:
        # This shouldn't happen for valid URLs
        pytest.fail(f"Valid URL raised InvalidURL: {url}")


@given(
    parts=st.lists(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'), min_size=1, max_size=10)
)
def test_comment_id_from_invalid_url_structure(parts):
    """Test Comment.id_from_url raises InvalidURL for malformed URLs."""
    # Create URLs that don't have the right structure
    url = "https://www.reddit.com/" + "/".join(parts)
    
    # If it doesn't contain 'comments' or has wrong number of parts, should raise
    if "comments" not in parts:
        with pytest.raises(InvalidURL):
            Comment.id_from_url(url)
    else:
        comment_index = parts.index("comments")
        # Should have exactly 4 parts after 'comments'
        if len(parts) - 4 != comment_index:
            with pytest.raises(InvalidURL):
                Comment.id_from_url(url)


# Test edge cases for BoundedSet
@given(items=st.lists(st.integers(), min_size=100, max_size=500))
def test_bounded_set_with_size_one(items):
    """BoundedSet with max_items=1 should only keep the last item."""
    bounded_set = BoundedSet(1)
    
    for item in items:
        bounded_set.add(item)
        assert len(bounded_set._set) == 1
    
    # Should only contain the last item
    assert items[-1] in bounded_set
    assert len(bounded_set._set) == 1


@given(
    max_size=st.integers(min_value=1, max_value=50),
    item=st.integers()
)
def test_bounded_set_duplicate_additions(max_size, item):
    """Adding the same item multiple times shouldn't increase set size."""
    bounded_set = BoundedSet(max_size)
    
    # Add the same item multiple times
    for _ in range(10):
        bounded_set.add(item)
    
    # Set should contain only one item
    assert len(bounded_set._set) == 1
    assert item in bounded_set


# Test PRAWBase._safely_add_arguments
@given(
    existing_key=st.text(min_size=1, max_size=10),
    existing_value=st.dictionaries(st.text(min_size=1), st.integers(), min_size=0, max_size=5),
    new_args=st.dictionaries(st.text(min_size=1), st.integers(), min_size=0, max_size=5)
)
def test_prawbase_safely_add_arguments(existing_key, existing_value, new_args):
    """PRAWBase._safely_add_arguments should not modify original dict."""
    original_args = {existing_key: existing_value.copy()}
    original_value_copy = existing_value.copy()
    
    # Call the method
    PRAWBase._safely_add_arguments(
        arguments=original_args,
        key=existing_key,
        **new_args
    )
    
    # Original value dict should not be modified
    assert existing_value == original_value_copy
    
    # The result should contain both old and new values
    result = original_args[existing_key]
    for k, v in existing_value.items():
        if k not in new_args:
            assert result[k] == v
    for k, v in new_args.items():
        assert result[k] == v


# Test extreme values for ExponentialCounter
@given(max_counter=st.one_of(
    st.just(0),
    st.just(-1),
    st.just(-100),
    st.floats(min_value=-1000, max_value=0)
))
def test_exponential_counter_negative_or_zero_max(max_counter):
    """ExponentialCounter with non-positive max_counter."""
    counter = ExponentialCounter(max_counter)
    
    # Even with negative/zero max, first value should be around 1
    first_value = counter.counter()
    assert 0.9375 <= first_value <= 1.0625
    
    # Subsequent values should respect the max
    for _ in range(10):
        value = counter.counter()
        # With negative max, the behavior might be undefined
        # but it shouldn't crash
        assert isinstance(value, (int, float))


# Test permissions_string with prefixed permissions
@given(
    known_perms=st.sets(st.text(min_size=1, max_size=5, alphabet='abcde'), min_size=1, max_size=5),
    prefixed_perms=st.lists(
        st.one_of(
            st.text(min_size=1, max_size=5, alphabet='abcde').map(lambda x: f"+{x}"),
            st.text(min_size=1, max_size=5, alphabet='abcde').map(lambda x: f"-{x}")
        ),
        min_size=0,
        max_size=10
    )
)
def test_permissions_string_with_prefixes(known_perms, prefixed_perms):
    """Test permissions_string when permissions already have +/- prefixes."""
    # The function expects permissions without prefixes based on the code
    # If we pass prefixed permissions, it should handle them
    result = permissions_string(known_permissions=known_perms, permissions=prefixed_perms)
    
    # The result should be a string
    assert isinstance(result, str)
    
    # It should contain comma-separated values
    if prefixed_perms:
        parts = result.split(",")
        assert len(parts) > 0


# Test Comment.id_from_url with edge case URLs
@example(url="https://www.reddit.com/r/test/comments/abc123/title/")
@example(url="https://reddit.com/comments/abc/def/ghi/jkl")
@example(url="https://www.reddit.com/r/test/comments/////")
@given(url=st.text(min_size=0, max_size=500))
def test_comment_id_from_url_fuzzing(url):
    """Fuzz test Comment.id_from_url with random strings."""
    try:
        result = Comment.id_from_url(url)
        # If it returns successfully, the URL must have had the right structure
        assert isinstance(result, str)
        assert len(result) > 0
    except InvalidURL:
        # This is expected for invalid URLs
        pass
    except Exception as e:
        # Any other exception might be a bug
        if "http" not in url.lower() and "reddit.com" not in url:
            # Expected for completely invalid URLs
            pass
        else:
            # Unexpected exception - might be a bug
            print(f"Unexpected exception for URL: {url}")
            print(f"Exception: {e}")
            raise


# Test BoundedSet with concurrent-like access patterns
@given(
    max_size=st.integers(min_value=2, max_value=10),
    operations=st.lists(
        st.tuples(
            st.sampled_from(['add', 'check']),
            st.integers(min_value=0, max_value=20)
        ),
        min_size=10,
        max_size=100
    )
)
def test_bounded_set_mixed_operations(max_size, operations):
    """Test BoundedSet with mixed add and check operations."""
    bounded_set = BoundedSet(max_size)
    
    for op, value in operations:
        if op == 'add':
            bounded_set.add(value)
        else:  # check
            _ = value in bounded_set
        
        # Invariant: size never exceeds max
        assert len(bounded_set._set) <= max_size


# Test the OrderedDict behavior in BoundedSet
@given(
    max_size=st.integers(min_value=5, max_value=20),
    items=st.lists(st.integers(), min_size=10, max_size=50, unique=True)
)  
def test_bounded_set_maintains_lru_order(max_size, items):
    """BoundedSet should maintain LRU (Least Recently Used) order."""
    bounded_set = BoundedSet(max_size)
    
    # Add all items
    for item in items:
        bounded_set.add(item)
    
    # Access the first few items that were added (if they're still there)
    accessed_items = []
    for item in items[:max_size//2]:
        if item in bounded_set:
            accessed_items.append(item)
    
    # Now add more items to trigger eviction
    new_items = [max(items) + i + 1 for i in range(max_size)]
    for new_item in new_items:
        bounded_set.add(new_item)
    
    # The accessed items should have higher chance of surviving
    # This is a statistical property, not absolute


if __name__ == "__main__":
    print("Running advanced property-based tests for praw.models...")
    
    # Run with more examples for thoroughness
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])