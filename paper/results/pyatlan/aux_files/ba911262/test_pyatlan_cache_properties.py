#!/usr/bin/env python3
"""Property-based tests for pyatlan.cache module using Hypothesis."""

import sys
import string
from unittest.mock import Mock, MagicMock
from typing import Dict

from hypothesis import given, strategies as st, assume, settings

# Add the virtual environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

# Import the cache modules
from pyatlan.cache.connection_cache import ConnectionName
from pyatlan.cache.custom_metadata_cache import CustomMetadataCache
from pyatlan.cache.user_cache import UserCache
from pyatlan.cache.abstract_asset_cache import AbstractAssetCache
from pyatlan.model.assets import Asset


# Test 1: ConnectionName parsing round-trip property
@given(
    st.text(
        alphabet=string.ascii_letters + string.digits + "-_",
        min_size=1,
        max_size=50
    ).filter(lambda x: x.strip()),
    st.text(
        alphabet=string.ascii_letters + string.digits + "-_. ",
        min_size=1,
        max_size=100
    ).filter(lambda x: x.strip())
)
def test_connection_name_round_trip(conn_type: str, conn_name: str):
    """Test that ConnectionName parsing and stringifying is a round-trip."""
    # Create a connection string
    connection_str = f"{conn_type}/{conn_name}"
    
    # Parse it
    conn_name_obj = ConnectionName(connection_str)
    
    # Convert back to string
    result = str(conn_name_obj)
    
    # The round-trip should preserve the format
    # Note: The type might be converted (e.g., to match enum values)
    # So we check that parsing the result gives the same object
    reparsed = ConnectionName(result)
    assert conn_name_obj == reparsed
    assert conn_name_obj.name == reparsed.name
    assert conn_name_obj.type == reparsed.type


# Test 2: ConnectionName edge cases with multiple slashes
@given(
    st.lists(
        st.text(
            alphabet=string.ascii_letters + string.digits + "-_",
            min_size=1,
            max_size=20
        ).filter(lambda x: x.strip()),
        min_size=2,
        max_size=5
    )
)
def test_connection_name_multiple_slashes(parts: list):
    """Test ConnectionName parsing with multiple slashes."""
    # Create a string with multiple parts separated by slashes
    connection_str = "/".join(parts)
    
    # Parse it
    conn_name_obj = ConnectionName(connection_str)
    
    # The first part should be the type, rest should be the name
    if conn_name_obj.type is not None and conn_name_obj.name is not None:
        # Check that type is derived from first part
        # and name is everything after the first slash
        expected_name = connection_str[len(parts[0]) + 1:]
        assert conn_name_obj.name == expected_name


# Test 3: CustomMetadataCache bidirectional map consistency
@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        values=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        min_size=0,
        max_size=20
    )
)
def test_custom_metadata_cache_bidirectional_consistency(id_to_name_data: Dict[str, str]):
    """Test that CustomMetadataCache maintains bidirectional map consistency."""
    # Create a mock client
    mock_client = Mock()
    
    # Create cache
    cache = CustomMetadataCache(mock_client)
    
    # Manually populate the maps (simulating what _refresh_cache would do)
    cache.map_id_to_name = id_to_name_data.copy()
    cache.map_name_to_id = {}
    
    # Build reverse map
    for id_val, name_val in id_to_name_data.items():
        # In real implementation, duplicate names would raise an error
        # We'll skip duplicates for this test
        if name_val not in cache.map_name_to_id:
            cache.map_name_to_id[name_val] = id_val
    
    # Property: For every id->name mapping, there should be a name->id mapping
    for id_val, name_val in cache.map_id_to_name.items():
        if name_val in cache.map_name_to_id:
            reverse_id = cache.map_name_to_id[name_val]
            # The reverse lookup should give us back an id
            # (might be different if there were duplicates, but should exist)
            assert reverse_id in cache.map_id_to_name


# Test 4: UserCache bidirectional map consistency
@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),  # user ids
        values=st.tuples(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),  # usernames
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '@' not in x) 
            .map(lambda x: f"{x}@example.com")  # emails
        ),
        min_size=0,
        max_size=20
    )
)
def test_user_cache_bidirectional_consistency(user_data: Dict[str, tuple]):
    """Test that UserCache maintains bidirectional map consistency."""
    # Create a mock client
    mock_client = Mock()
    mock_client.token = Mock()
    mock_client.token.get_by_id = Mock(return_value=None)
    
    # Create cache
    cache = UserCache(mock_client)
    
    # Populate the maps
    for user_id, (username, email) in user_data.items():
        cache.map_id_to_name[user_id] = username
        cache.map_name_to_id[username] = user_id
        cache.map_email_to_id[email] = user_id
    
    # Property 1: id->name and name->id should be consistent
    for user_id, username in cache.map_id_to_name.items():
        if username in cache.map_name_to_id:
            assert cache.map_name_to_id[username] == user_id
    
    # Property 2: email->id should map to valid users
    for email, user_id in cache.map_email_to_id.items():
        assert user_id in cache.map_id_to_name


# Test 5: AbstractAssetCache consistency invariant
class TestAssetCache(AbstractAssetCache):
    """Concrete implementation for testing."""
    
    def lookup_by_guid(self, guid: str):
        pass
    
    def lookup_by_qualified_name(self, qualified_name: str):
        pass
    
    def lookup_by_name(self, name):
        pass
    
    def get_name(self, asset: Asset):
        return asset.name if hasattr(asset, 'name') else None


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),  # guid
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),  # name
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),  # qualified_name
        ),
        min_size=0,
        max_size=20,
        unique_by=lambda x: x[0]  # unique by guid
    )
)
def test_abstract_asset_cache_consistency(asset_data: list):
    """Test that AbstractAssetCache maintains consistency across its three dictionaries."""
    # Create a mock client
    mock_client = Mock()
    
    # Create cache
    cache = TestAssetCache(mock_client)
    
    # Create and cache mock assets
    for guid, name, qualified_name in asset_data:
        mock_asset = Mock(spec=Asset)
        mock_asset.guid = guid
        mock_asset.name = name
        mock_asset.qualified_name = qualified_name
        
        # Cache the asset
        cache.cache(mock_asset)
    
    # Property: All three dictionaries should be consistent
    for name, guid in cache.name_to_guid.items():
        # The guid should exist in guid_to_asset
        assert guid in cache.guid_to_asset
        
        # The asset should have the correct name
        asset = cache.guid_to_asset[guid]
        assert asset.name == name
        
        # The qualified_name should map to the same guid
        assert cache.qualified_name_to_guid.get(asset.qualified_name) == guid
    
    # Reverse check: every guid_to_asset entry should be in other maps
    for guid, asset in cache.guid_to_asset.items():
        if asset.name:  # get_name might return None
            assert cache.name_to_guid.get(asset.name) == guid
        assert cache.qualified_name_to_guid.get(asset.qualified_name) == guid


# Test 6: CustomMetadataCache whitespace handling
@given(
    st.sampled_from(["", " ", "  ", "\t", "\n", " \t\n ", "   \t   "])
)
def test_custom_metadata_cache_empty_string_handling(whitespace: str):
    """Test that CustomMetadataCache properly handles empty/whitespace strings."""
    from pyatlan.errors import ErrorCode, InvalidRequestException
    
    # Create a mock client
    mock_client = Mock()
    
    # Create cache
    cache = CustomMetadataCache(mock_client)
    
    # These methods should raise errors for empty/whitespace strings
    try:
        # Based on the code, _get_id_for_name checks: if name is None or not name.strip()
        result = cache._get_id_for_name(whitespace)
        # If we get here without exception, it's a bug
        # The code clearly shows it should raise MISSING_CM_NAME
        assert False, f"Expected exception for whitespace input '{repr(whitespace)}'"
    except Exception as e:
        # Should raise the appropriate error
        # The code shows: raise ErrorCode.MISSING_CM_NAME.exception_with_parameters()
        assert "MISSING_CM_NAME" in str(type(e)) or "missing" in str(e).lower()


# Test 7: CustomMetadataCache get_name_for_id empty string handling  
@given(
    st.sampled_from(["", " ", "  ", "\t", "\n", " \t\n ", "   \t   "])
)
def test_custom_metadata_cache_get_name_for_id_empty(whitespace: str):
    """Test that get_name_for_id properly handles empty/whitespace strings."""
    from pyatlan.errors import ErrorCode
    
    # Create a mock client
    mock_client = Mock()
    
    # Create cache
    cache = CustomMetadataCache(mock_client)
    
    # Should raise error for empty/whitespace strings
    try:
        result = cache._get_name_for_id(whitespace)
        assert False, f"Expected exception for whitespace input '{repr(whitespace)}'"
    except Exception as e:
        # Should raise MISSING_CM_ID error
        assert "MISSING_CM_ID" in str(type(e)) or "missing" in str(e).lower()


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v"])