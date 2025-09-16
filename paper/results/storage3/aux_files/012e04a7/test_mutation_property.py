"""Property-based test demonstrating the mutability bug in storage3.constants."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import storage3.constants
from storage3.constants import DEFAULT_SEARCH_OPTIONS, DEFAULT_FILE_OPTIONS, DEFAULT_TIMEOUT


@given(
    new_limit=st.integers(),
    new_offset=st.integers(),
    new_column=st.text(min_size=1),
    new_order=st.text(min_size=1)
)
def test_search_options_mutability_bug(new_limit, new_offset, new_column, new_order):
    """DEFAULT_SEARCH_OPTIONS can be mutated, affecting all code using it."""
    
    # Save originals
    original = dict(DEFAULT_SEARCH_OPTIONS)
    original_sortby = dict(DEFAULT_SEARCH_OPTIONS["sortBy"])
    
    # Mutate the "constant"
    DEFAULT_SEARCH_OPTIONS["limit"] = new_limit
    DEFAULT_SEARCH_OPTIONS["offset"] = new_offset
    DEFAULT_SEARCH_OPTIONS["sortBy"]["column"] = new_column
    DEFAULT_SEARCH_OPTIONS["sortBy"]["order"] = new_order
    
    # The mutation persists
    assert DEFAULT_SEARCH_OPTIONS["limit"] == new_limit
    assert DEFAULT_SEARCH_OPTIONS["offset"] == new_offset
    assert DEFAULT_SEARCH_OPTIONS["sortBy"]["column"] == new_column
    assert DEFAULT_SEARCH_OPTIONS["sortBy"]["order"] == new_order
    
    # New imports see the mutated value
    from storage3.constants import DEFAULT_SEARCH_OPTIONS as reimported
    assert reimported["limit"] == new_limit
    
    # Any code using DEFAULT_SEARCH_OPTIONS now gets wrong values
    # This could break the entire storage3 library!
    
    # Restore to avoid breaking other tests
    DEFAULT_SEARCH_OPTIONS.clear()
    DEFAULT_SEARCH_OPTIONS.update(original)
    DEFAULT_SEARCH_OPTIONS["sortBy"] = original_sortby


@given(
    cache_control=st.text(),
    content_type=st.text(),
    x_upsert=st.text()
)
def test_file_options_mutability_bug(cache_control, content_type, x_upsert):
    """DEFAULT_FILE_OPTIONS can be mutated, affecting all code using it."""
    
    # Save originals
    original = dict(DEFAULT_FILE_OPTIONS)
    
    # Mutate the "constant"
    DEFAULT_FILE_OPTIONS["cache-control"] = cache_control
    DEFAULT_FILE_OPTIONS["content-type"] = content_type
    DEFAULT_FILE_OPTIONS["x-upsert"] = x_upsert
    
    # The mutation persists
    assert DEFAULT_FILE_OPTIONS["cache-control"] == cache_control
    assert DEFAULT_FILE_OPTIONS["content-type"] == content_type
    assert DEFAULT_FILE_OPTIONS["x-upsert"] == x_upsert
    
    # This affects all HTTP headers sent by the library!
    
    # Restore
    DEFAULT_FILE_OPTIONS.clear()
    DEFAULT_FILE_OPTIONS.update(original)


def test_timeout_is_immutable():
    """DEFAULT_TIMEOUT is an integer, so it's actually immutable (good)."""
    original = DEFAULT_TIMEOUT
    
    # This creates a new binding, doesn't mutate the original
    storage3.constants.DEFAULT_TIMEOUT = 999
    
    # Re-importing gets the new value
    from storage3.constants import DEFAULT_TIMEOUT as reimported
    assert reimported == 999
    
    # But this is module-level rebinding, not mutation of the value itself
    # Integers are immutable in Python, so this is expected behavior
    
    # Restore
    storage3.constants.DEFAULT_TIMEOUT = original


if __name__ == "__main__":
    # Run a simple demonstration
    print("Before mutation:", DEFAULT_SEARCH_OPTIONS)
    DEFAULT_SEARCH_OPTIONS["limit"] = 666
    print("After mutation:", DEFAULT_SEARCH_OPTIONS)
    
    # The bug is that anyone can change these "constants"
    DEFAULT_SEARCH_OPTIONS["limit"] = 100  # Restore