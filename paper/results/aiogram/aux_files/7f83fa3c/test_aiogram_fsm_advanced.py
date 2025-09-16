import asyncio
from typing import Any, Optional

import pytest
from hypothesis import given, strategies as st, settings, assume

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.state import State, StatesGroup


# Create sample states for testing
class TestStates(StatesGroup):
    """Sample states for testing"""
    waiting_for_input = State()
    processing = State()
    completed = State()


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


class TestMemoryStorageWithStates:
    """Test MemoryStorage with State objects"""

    @given(
        key=storage_key_strategy
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_set_state_with_state_object(self, key: StorageKey):
        """Property: set_state should work with State objects"""
        storage = MemoryStorage()
        
        # Set state using State object
        await storage.set_state(key, TestStates.waiting_for_input)
        
        # Should retrieve the state string
        state_str = await storage.get_state(key)
        assert state_str == TestStates.waiting_for_input.state
        assert isinstance(state_str, str)

    @given(
        key=storage_key_strategy,
        state_str=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_state_string_round_trip(self, key: StorageKey, state_str: str):
        """Property: state strings should round-trip correctly"""
        storage = MemoryStorage()
        
        # Set state as string
        await storage.set_state(key, state_str)
        
        # Get it back
        retrieved = await storage.get_state(key)
        assert retrieved == state_str

    @given(
        key=storage_key_strategy
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_clear_state_with_none(self, key: StorageKey):
        """Property: setting state to None should clear it"""
        storage = MemoryStorage()
        
        # Set initial state
        await storage.set_state(key, "some_state")
        assert await storage.get_state(key) == "some_state"
        
        # Clear state with None
        await storage.set_state(key, None)
        assert await storage.get_state(key) is None

    @given(
        key=storage_key_strategy,
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.integers(),
            min_size=1,
            max_size=10
        ),
        state=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_state_and_data_independence(self, key: StorageKey, data: dict, state: str):
        """Property: state and data should be independent"""
        storage = MemoryStorage()
        
        # Set state and data
        await storage.set_state(key, state)
        await storage.set_data(key, data)
        
        # Both should be retrievable
        assert await storage.get_state(key) == state
        assert await storage.get_data(key) == data
        
        # Clearing state shouldn't affect data
        await storage.set_state(key, None)
        assert await storage.get_state(key) is None
        assert await storage.get_data(key) == data
        
        # Setting new data shouldn't affect state
        await storage.set_state(key, state)
        await storage.set_data(key, {'new': 'data'})
        assert await storage.get_state(key) == state

    @given(
        keys=st.lists(
            storage_key_strategy,
            min_size=2,
            max_size=5,
            unique=True
        ),
        states=st.lists(
            st.text(min_size=1, max_size=50),
            min_size=2,
            max_size=5
        )
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_concurrent_access(self, keys: list, states: list):
        """Property: concurrent access to different keys should work correctly"""
        storage = MemoryStorage()
        
        # Ensure we have same number of keys and states
        states = states[:len(keys)]
        
        async def set_and_get(key: StorageKey, state: str):
            await storage.set_state(key, state)
            await storage.set_data(key, {'state': state})
            retrieved_state = await storage.get_state(key)
            retrieved_data = await storage.get_data(key)
            return retrieved_state == state and retrieved_data == {'state': state}
        
        # Run concurrently
        tasks = [set_and_get(key, state) for key, state in zip(keys, states)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(results)

    @given(
        key=storage_key_strategy,
        special_chars=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=1,
            max_size=50
        ).filter(lambda x: x.strip())  # Ensure non-empty after strip
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_special_characters_in_data(self, key: StorageKey, special_chars: str):
        """Property: storage should handle special characters in data"""
        storage = MemoryStorage()
        
        data = {
            special_chars: 'value',
            'key': special_chars,
            'emoji': '🚀🔥💻',
            'unicode': 'ñáéíóú'
        }
        
        # Set and retrieve
        await storage.set_data(key, data)
        retrieved = await storage.get_data(key)
        
        assert retrieved == data

    @given(
        key=storage_key_strategy,
        value=st.recursive(
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(max_size=50)
            ),
            lambda children: st.one_of(
                st.lists(children, max_size=5),
                st.dictionaries(
                    st.text(min_size=1, max_size=10),
                    children,
                    max_size=5
                )
            ),
            max_leaves=20
        )
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_deeply_nested_structures(self, key: StorageKey, value: Any):
        """Property: storage should handle deeply nested structures"""
        storage = MemoryStorage()
        
        data = {'nested': value}
        
        # Set and retrieve
        await storage.set_data(key, data)
        retrieved = await storage.get_data(key)
        
        assert retrieved == data

    @given(
        key=storage_key_strategy,
        large_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=100, max_size=500),
            min_size=10,
            max_size=20
        )
    )
    @settings(max_examples=10)
    @pytest.mark.asyncio
    async def test_large_data_handling(self, key: StorageKey, large_data: dict):
        """Property: storage should handle large data correctly"""
        storage = MemoryStorage()
        
        # Set large data
        await storage.set_data(key, large_data)
        
        # Should retrieve correctly
        retrieved = await storage.get_data(key)
        assert retrieved == large_data
        
        # Update with more large data
        more_data = {'extra_' + k: v for k, v in large_data.items()}
        result = await storage.update_data(key, more_data)
        
        expected = large_data.copy()
        expected.update(more_data)
        assert result == expected