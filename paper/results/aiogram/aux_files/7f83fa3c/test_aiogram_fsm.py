import asyncio
from collections.abc import Mapping
from typing import Dict, Any

import pytest
from hypothesis import given, strategies as st, assume, settings

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey


# Strategies for generating test data
storage_key_strategy = st.builds(
    StorageKey,
    bot_id=st.integers(min_value=1, max_value=2**31-1),
    chat_id=st.integers(min_value=-2**63, max_value=2**63-1),
    user_id=st.integers(min_value=1, max_value=2**31-1),
    thread_id=st.one_of(st.none(), st.integers(min_value=1, max_value=2**31-1)),
    business_connection_id=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    destiny=st.text(min_size=1, max_size=50)
)

# Strategy for valid data (must be dict-like)
valid_data_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100),
        st.lists(st.integers(), max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5)
    ),
    max_size=20
)


class TestMemoryStorage:
    """Test properties of MemoryStorage implementation"""

    @given(
        key=storage_key_strategy,
        data=valid_data_strategy
    )
    @settings(max_examples=500)
    @pytest.mark.asyncio
    async def test_set_get_data_round_trip(self, key: StorageKey, data: Dict[str, Any]):
        """Property: data that is set can be retrieved exactly"""
        storage = MemoryStorage()
        
        # Set data
        await storage.set_data(key, data)
        
        # Get data back
        retrieved = await storage.get_data(key)
        
        # Should be equal
        assert retrieved == data

    @given(
        key1=storage_key_strategy,
        key2=storage_key_strategy,
        data1=valid_data_strategy,
        data2=valid_data_strategy
    )
    @settings(max_examples=200)
    @pytest.mark.asyncio
    async def test_key_isolation(self, key1: StorageKey, key2: StorageKey, 
                                  data1: Dict[str, Any], data2: Dict[str, Any]):
        """Property: data stored under different keys should be isolated"""
        assume(key1 != key2)  # Keys must be different
        
        storage = MemoryStorage()
        
        # Set data for both keys
        await storage.set_data(key1, data1)
        await storage.set_data(key2, data2)
        
        # Each key should retrieve its own data
        assert await storage.get_data(key1) == data1
        assert await storage.get_data(key2) == data2

    @given(
        key=storage_key_strategy,
        data=valid_data_strategy
    )
    @settings(max_examples=200)
    @pytest.mark.asyncio
    async def test_get_data_returns_copy(self, key: StorageKey, data: Dict[str, Any]):
        """Property: get_data should return a copy that doesn't affect storage"""
        storage = MemoryStorage()
        
        # Set initial data
        await storage.set_data(key, data)
        
        # Get data and modify it
        retrieved1 = await storage.get_data(key)
        retrieved1['test_key'] = 'modified_value'
        retrieved1.clear()  # Extreme modification
        
        # Get data again - should be unaffected
        retrieved2 = await storage.get_data(key)
        assert retrieved2 == data

    @given(
        key=storage_key_strategy,
        initial_data=valid_data_strategy,
        update_data=valid_data_strategy
    )
    @settings(max_examples=200)
    @pytest.mark.asyncio
    async def test_update_data_preserves_existing(self, key: StorageKey,
                                                   initial_data: Dict[str, Any],
                                                   update_data: Dict[str, Any]):
        """Property: update_data should merge data, preserving non-conflicting keys"""
        storage = MemoryStorage()
        
        # Set initial data
        await storage.set_data(key, initial_data)
        
        # Update with new data
        result = await storage.update_data(key, update_data)
        
        # Result should be the merge
        expected = initial_data.copy()
        expected.update(update_data)
        assert result == expected
        
        # Storage should also contain the merged data
        assert await storage.get_data(key) == expected

    @given(
        key=storage_key_strategy,
        data=valid_data_strategy,
        existing_key=st.text(min_size=1, max_size=50),
        missing_key=st.text(min_size=1, max_size=50),
        default_value=st.one_of(st.none(), st.integers(), st.text())
    )
    @settings(max_examples=200)
    @pytest.mark.asyncio
    async def test_get_value_with_defaults(self, key: StorageKey, data: Dict[str, Any],
                                            existing_key: str, missing_key: str,
                                            default_value: Any):
        """Property: get_value should return correct values and defaults"""
        assume(existing_key != missing_key)
        assume(missing_key not in data)
        
        storage = MemoryStorage()
        
        # Prepare data with a known key
        data[existing_key] = 'known_value'
        await storage.set_data(key, data)
        
        # Getting existing key should return its value
        assert await storage.get_value(key, existing_key) == 'known_value'
        
        # Getting missing key with default should return default
        assert await storage.get_value(key, missing_key, default_value) == default_value
        
        # Getting missing key without default should return None
        assert await storage.get_value(key, missing_key) is None

    @given(
        key=storage_key_strategy,
        state=st.one_of(st.none(), st.text(min_size=1, max_size=100))
    )
    @settings(max_examples=200)
    @pytest.mark.asyncio
    async def test_state_persistence(self, key: StorageKey, state: str):
        """Property: set_state/get_state should maintain state correctly"""
        storage = MemoryStorage()
        
        # Set state
        await storage.set_state(key, state)
        
        # Get state back
        retrieved = await storage.get_state(key)
        
        assert retrieved == state

    @given(
        key=storage_key_strategy,
        data=valid_data_strategy
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_update_data_returns_copy(self, key: StorageKey, data: Dict[str, Any]):
        """Property: update_data should return a copy that doesn't affect storage"""
        storage = MemoryStorage()
        
        # Set initial data
        await storage.set_data(key, {'initial': 'value'})
        
        # Update and get result
        result = await storage.update_data(key, data)
        
        # Modify returned result
        result['modified'] = 'after_return'
        result.clear()
        
        # Storage should be unaffected
        stored = await storage.get_data(key)
        expected = {'initial': 'value'}
        expected.update(data)
        assert stored == expected

    @given(
        key=storage_key_strategy
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_empty_storage_returns_empty_data(self, key: StorageKey):
        """Property: getting data from empty storage should return empty dict"""
        storage = MemoryStorage()
        
        # Get data without setting anything
        data = await storage.get_data(key)
        
        # Should be empty dict, not None
        assert data == {}
        assert isinstance(data, dict)

    @given(
        key=storage_key_strategy
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_empty_storage_returns_none_state(self, key: StorageKey):
        """Property: getting state from empty storage should return None"""
        storage = MemoryStorage()
        
        # Get state without setting anything
        state = await storage.get_state(key)
        
        assert state is None

    @given(
        key=storage_key_strategy,
        empty_dict=st.just({})
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_set_empty_data(self, key: StorageKey, empty_dict: Dict):
        """Property: setting empty dict should work and be retrievable"""
        storage = MemoryStorage()
        
        # Set empty dict
        await storage.set_data(key, empty_dict)
        
        # Should get empty dict back
        assert await storage.get_data(key) == {}

    @given(
        key=storage_key_strategy,
        initial_data=valid_data_strategy
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio  
    async def test_update_with_empty_dict(self, key: StorageKey, initial_data: Dict[str, Any]):
        """Property: updating with empty dict should preserve existing data"""
        storage = MemoryStorage()
        
        # Set initial data
        await storage.set_data(key, initial_data)
        
        # Update with empty dict
        result = await storage.update_data(key, {})
        
        # Should return original data
        assert result == initial_data
        assert await storage.get_data(key) == initial_data

    @given(
        key=storage_key_strategy,
        value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.lists(st.integers()),
            st.dictionaries(st.text(min_size=1), st.integers())
        )
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_get_value_returns_copy_of_mutable(self, key: StorageKey, value: Any):
        """Property: get_value should return a copy of mutable values"""
        storage = MemoryStorage()
        
        # Set data with a value
        await storage.set_data(key, {'test_key': value})
        
        # Get the value
        retrieved1 = await storage.get_value(key, 'test_key')
        
        # If it's mutable, try to modify it
        if isinstance(retrieved1, (list, dict)):
            if isinstance(retrieved1, list):
                retrieved1.append('modified')
            else:
                retrieved1['modified'] = True
            
            # Get value again - should be unmodified
            retrieved2 = await storage.get_value(key, 'test_key')
            assert retrieved2 == value