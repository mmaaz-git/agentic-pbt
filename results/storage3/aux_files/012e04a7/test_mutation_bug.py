"""Demonstrate the mutation bug in storage3.constants."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

from storage3.constants import DEFAULT_SEARCH_OPTIONS, DEFAULT_FILE_OPTIONS


def test_constants_are_mutable():
    """Constants should be immutable but they are not."""
    
    # Get the original values
    original_limit = DEFAULT_SEARCH_OPTIONS["limit"]
    original_cache_control = DEFAULT_FILE_OPTIONS["cache-control"]
    
    print(f"Original limit: {original_limit}")
    print(f"Original cache-control: {original_cache_control}")
    
    # Modify the "constants" directly
    DEFAULT_SEARCH_OPTIONS["limit"] = 999999
    DEFAULT_FILE_OPTIONS["cache-control"] = "malicious"
    
    # The constants have been mutated!
    print(f"Modified limit: {DEFAULT_SEARCH_OPTIONS['limit']}")
    print(f"Modified cache-control: {DEFAULT_FILE_OPTIONS['cache-control']}")
    
    assert DEFAULT_SEARCH_OPTIONS["limit"] == 999999
    assert DEFAULT_FILE_OPTIONS["cache-control"] == "malicious"
    
    # This affects all future uses of these "constants"
    from storage3.constants import DEFAULT_SEARCH_OPTIONS as NEW_IMPORT
    assert NEW_IMPORT["limit"] == 999999  # The mutation persists!
    
    print("BUG CONFIRMED: Constants are mutable and can be modified!")
    
    # Restore for other tests
    DEFAULT_SEARCH_OPTIONS["limit"] = original_limit
    DEFAULT_FILE_OPTIONS["cache-control"] = original_cache_control


if __name__ == "__main__":
    test_constants_are_mutable()