#!/usr/bin/env python3
"""Minimal reproduction scripts for bugs found in pyatlan.cache."""

import sys
from unittest.mock import Mock

# Add the virtual environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.cache.abstract_asset_cache import AbstractAssetCache
from pyatlan.cache.user_cache import UserCache
from pyatlan.model.assets import Asset


# Bug 1: AbstractAssetCache overwrites entries when names or qualified_names collide
print("=== Bug 1: AbstractAssetCache cache collision bug ===")
print("When multiple assets have the same name or qualified_name but different GUIDs,")
print("the cache becomes inconsistent and returns wrong assets.\n")

class ConcreteAssetCache(AbstractAssetCache):
    def lookup_by_guid(self, guid: str):
        pass
    def lookup_by_qualified_name(self, qualified_name: str):
        pass
    def lookup_by_name(self, name):
        pass
    def get_name(self, asset: Asset):
        return asset.name if hasattr(asset, 'name') else None

# Create cache
mock_client = Mock()
cache = ConcreteAssetCache(mock_client)

# Create two assets with same name but different GUIDs
asset1 = Mock(spec=Asset)
asset1.guid = "guid-1"
asset1.name = "same-name"
asset1.qualified_name = "qualified-1"

asset2 = Mock(spec=Asset)
asset2.guid = "guid-2"
asset2.name = "same-name"  # Same name as asset1!
asset2.qualified_name = "qualified-2"

# Cache both assets
cache.cache(asset1)
cache.cache(asset2)

# Check the cache state
print(f"name_to_guid['same-name'] = {cache.name_to_guid.get('same-name')}")
print(f"Expected: 'guid-1' (first asset) or error")
print(f"Actual: 'guid-2' (second asset overwrote first)\n")

# Try to retrieve first asset by name
print("Retrieving asset by name 'same-name':")
guid = cache.name_to_guid.get('same-name')
asset = cache.guid_to_asset.get(guid)
print(f"Expected asset with guid='guid-1', got guid='{asset.guid}'")
print("BUG: First asset is lost, second asset overwrote it!\n")

# Bug 2: Similar issue with qualified_name collisions
asset3 = Mock(spec=Asset)
asset3.guid = "guid-3"
asset3.name = "name-3"
asset3.qualified_name = "same-qualified"

asset4 = Mock(spec=Asset)
asset4.guid = "guid-4"
asset4.name = "name-4"
asset4.qualified_name = "same-qualified"  # Same qualified_name!

cache.cache(asset3)
cache.cache(asset4)

print("=== Qualified name collision ===")
print(f"qualified_name_to_guid['same-qualified'] = {cache.qualified_name_to_guid.get('same-qualified')}")
print(f"Expected: 'guid-3' or error, Actual: 'guid-4' (overwrote)")
print()

# Bug 3: UserCache overwrites entries when usernames collide
print("\n=== Bug 2: UserCache username collision bug ===")
print("When multiple user IDs map to the same username,")
print("the cache becomes inconsistent.\n")

# Create UserCache
user_cache = UserCache(mock_client)
mock_client.token = Mock()
mock_client.token.get_by_id = Mock(return_value=None)

# Simulate two users with different IDs but same username
# This could happen if usernames are reused after deletion
user_cache.map_id_to_name["user-id-1"] = "john.doe"
user_cache.map_name_to_id["john.doe"] = "user-id-1"

# Now a second user with same username
user_cache.map_id_to_name["user-id-2"] = "john.doe"
user_cache.map_name_to_id["john.doe"] = "user-id-2"  # Overwrites!

print("After adding two users with same username:")
print(f"map_id_to_name['user-id-1'] = '{user_cache.map_id_to_name['user-id-1']}'")
print(f"map_id_to_name['user-id-2'] = '{user_cache.map_id_to_name['user-id-2']}'")
print(f"map_name_to_id['john.doe'] = '{user_cache.map_name_to_id['john.doe']}'")
print()
print("BUG: Both user-id-1 and user-id-2 have username 'john.doe',")
print("but map_name_to_id can only store one mapping!")
print("This breaks bidirectional consistency and lookups.")