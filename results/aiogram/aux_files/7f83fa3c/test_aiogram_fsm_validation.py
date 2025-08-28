import asyncio
from typing import Any

import pytest
from hypothesis import given, strategies as st, settings

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey


# Strategy for storage keys
storage_key_strategy = st.builds(
    StorageKey,
    bot_id=st.integers(min_value=1, max_value=2**31-1),
    chat_id=st.integers(min_value=-2**63, max_value=2**63-1),
    user_id=st.integers(min_value=1, max_value=2**31-1),
    thread_id=st.one_of(st.none(), st.integers(min_value=1, max_value=2**31-1)),
    business_connection_id=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    destiny=st.text(min_size=1, max_size=50)
)

# Strategy for non-dict-like values
non_dict_strategy = st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.sets(st.integers()),
    st.binary()
)


class TestMemoryStorageValidation:
    """Test validation properties of MemoryStorage"""

    @given(
        key=storage_key_strategy,
        invalid_data=non_dict_strategy
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_set_data_rejects_non_dict(self, key: StorageKey, invalid_data: Any):
        """Property: set_data should only accept dict-like objects"""
        storage = MemoryStorage()
        
        # Should raise an error for non-dict data
        with pytest.raises(Exception) as exc_info:
            await storage.set_data(key, invalid_data)
        
        # Check that it's the expected error type
        assert "DataNotDictLikeError" in str(type(exc_info.value).__name__) or \
               "dict-like" in str(exc_info.value).lower() or \
               "must be a dict" in str(exc_info.value).lower()

    @given(
        key=storage_key_strategy
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_update_data_on_empty_storage(self, key: StorageKey):
        """Property: update_data on empty storage should create new data"""
        storage = MemoryStorage()
        
        # Update without setting initial data
        result = await storage.update_data(key, {'new': 'data'})
        
        # Should create the data
        assert result == {'new': 'data'}
        assert await storage.get_data(key) == {'new': 'data'}

    @given(
        key=storage_key_strategy,
        nested_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.dictionaries(
                keys=st.text(min_size=1, max_size=10),
                values=st.integers(),
                max_size=5
            ),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_nested_dict_copy_semantics(self, key: StorageKey, nested_data: dict):
        """Property: nested dicts should also be copied properly"""
        storage = MemoryStorage()
        
        # Set nested data
        await storage.set_data(key, nested_data)
        
        # Get data and modify nested structure
        retrieved = await storage.get_data(key)
        for outer_key in retrieved:
            if isinstance(retrieved[outer_key], dict):
                retrieved[outer_key]['modified'] = 999
                retrieved[outer_key].clear()
        
        # Original should be unaffected
        stored = await storage.get_data(key)
        assert stored == nested_data

    @given(
        key=storage_key_strategy,
        data1=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.integers(),
            min_size=5,
            max_size=10
        ),
        data2=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.integers(),
            min_size=5,
            max_size=10
        )
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_set_data_overwrites_completely(self, key: StorageKey, data1: dict, data2: dict):
        """Property: set_data should completely replace existing data, not merge"""
        storage = MemoryStorage()
        
        # Set first data
        await storage.set_data(key, data1)
        
        # Set second data
        await storage.set_data(key, data2)
        
        # Should only have data2, not a merge
        result = await storage.get_data(key)
        assert result == data2
        
        # Verify no keys from data1 that aren't in data2
        for key1 in data1:
            if key1 not in data2:
                assert key1 not in result