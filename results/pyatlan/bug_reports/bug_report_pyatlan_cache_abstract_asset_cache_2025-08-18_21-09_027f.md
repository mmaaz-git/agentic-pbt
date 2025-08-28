# Bug Report: AbstractAssetCache Silent Overwrite on Name Collisions

**Target**: `pyatlan.cache.abstract_asset_cache.AbstractAssetCache`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

AbstractAssetCache silently overwrites cached entries when assets have the same name or qualified_name but different GUIDs, leading to cache corruption and incorrect asset retrieval.

## Property-Based Test

```python
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
    cache = TestAssetCache(Mock())
    for guid, name, qualified_name in asset_data:
        mock_asset = Mock(spec=Asset)
        mock_asset.guid = guid
        mock_asset.name = name
        mock_asset.qualified_name = qualified_name
        cache.cache(mock_asset)
    
    # Property: All three dictionaries should be consistent
    for guid, asset in cache.guid_to_asset.items():
        if asset.name:
            assert cache.name_to_guid.get(asset.name) == guid
        assert cache.qualified_name_to_guid.get(asset.qualified_name) == guid
```

**Failing input**: `[('0', '0', '0'), ('1', '0', '0')]`

## Reproducing the Bug

```python
import sys
from unittest.mock import Mock
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.cache.abstract_asset_cache import AbstractAssetCache
from pyatlan.model.assets import Asset

class ConcreteAssetCache(AbstractAssetCache):
    def lookup_by_guid(self, guid: str): pass
    def lookup_by_qualified_name(self, qualified_name: str): pass
    def lookup_by_name(self, name): pass
    def get_name(self, asset: Asset):
        return asset.name if hasattr(asset, 'name') else None

cache = ConcreteAssetCache(Mock())

asset1 = Mock(spec=Asset)
asset1.guid = "guid-1"
asset1.name = "same-name"
asset1.qualified_name = "qualified-1"

asset2 = Mock(spec=Asset)
asset2.guid = "guid-2"
asset2.name = "same-name"
asset2.qualified_name = "qualified-2"

cache.cache(asset1)
cache.cache(asset2)

print(f"name_to_guid['same-name'] = {cache.name_to_guid.get('same-name')}")
print(f"Expected: 'guid-1', Actual: 'guid-2' (overwrote)")

retrieved_guid = cache.name_to_guid.get('same-name')
retrieved_asset = cache.guid_to_asset.get(retrieved_guid)
print(f"Retrieved asset guid: {retrieved_asset.guid}")
print("Bug: First asset is lost!")
```

## Why This Is A Bug

The cache assumes that asset names and qualified_names are unique, but silently overwrites entries when collisions occur. This violates cache consistency - multiple assets exist in `guid_to_asset` but only the last one is accessible via name or qualified_name lookups. This can cause the wrong asset to be returned from cache, potentially leading to data corruption or security issues if the wrong asset's permissions are used.

## Fix

```diff
--- a/pyatlan/cache/abstract_asset_cache.py
+++ b/pyatlan/cache/abstract_asset_cache.py
@@ -76,11 +76,20 @@ class AbstractAssetCache(ABC):
     def cache(self, asset: Asset):
         """
         Add an entry to the cache.
 
         :param asset: to be cached
+        :raises ValueError: if an asset with the same name or qualified_name but different guid already exists
         """
         name = asset and self.get_name(asset)
         if not all([name, asset.guid, asset.qualified_name]):
             return
+        
+        # Check for collisions
+        if name in self.name_to_guid and self.name_to_guid[name] != asset.guid:
+            raise ValueError(f"Asset with name '{name}' already exists with different GUID")
+        if asset.qualified_name in self.qualified_name_to_guid and self.qualified_name_to_guid[asset.qualified_name] != asset.guid:
+            raise ValueError(f"Asset with qualified_name '{asset.qualified_name}' already exists with different GUID")
+        
         self.name_to_guid[name] = asset.guid  # type: ignore[index]
         self.guid_to_asset[asset.guid] = asset  # type: ignore[index]
         self.qualified_name_to_guid[asset.qualified_name] = asset.guid  # type: ignore[index]
```