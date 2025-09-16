import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

import pytest
from hypothesis import given, strategies as st, settings, assume

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.state import State


# Strategy for generating test data
valid_data_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100),
        st.lists(st.integers(), max_size=10)
    ),
    max_size=20
)


def create_mock_fsm_context(storage_key: StorageKey):
    """Create a mock FSMContext with real MemoryStorage"""
    storage = MemoryStorage()
    
    # Create FSMContext with required parameters
    context = FSMContext(
        storage=storage,
        key=storage_key
    )
    
    return context, storage


class TestFSMContext:
    """Test FSMContext interaction with MemoryStorage"""

    @given(
        bot_id=st.integers(min_value=1, max_value=2**31-1),
        chat_id=st.integers(min_value=-2**63, max_value=2**63-1),
        user_id=st.integers(min_value=1, max_value=2**31-1),
        data=valid_data_strategy
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_context_data_round_trip(self, bot_id: int, chat_id: int, 
                                           user_id: int, data: Dict[str, Any]):
        """Property: FSMContext should correctly store and retrieve data"""
        key = StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
        context, storage = create_mock_fsm_context(key)
        
        # Set data through context
        await context.set_data(data)
        
        # Get data back through context
        retrieved = await context.get_data()
        assert retrieved == data
        
        # Verify it's also in storage
        storage_data = await storage.get_data(key)
        assert storage_data == data

    @given(
        bot_id=st.integers(min_value=1, max_value=2**31-1),
        chat_id=st.integers(min_value=-2**63, max_value=2**63-1),
        user_id=st.integers(min_value=1, max_value=2**31-1),
        initial_data=valid_data_strategy,
        update_data=valid_data_strategy
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_context_update_data(self, bot_id: int, chat_id: int, user_id: int,
                                       initial_data: Dict[str, Any], 
                                       update_data: Dict[str, Any]):
        """Property: FSMContext.update_data should merge data correctly"""
        key = StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
        context, storage = create_mock_fsm_context(key)
        
        # Set initial data
        await context.set_data(initial_data)
        
        # Update with new data
        result = await context.update_data(update_data)
        
        # Result should be merged
        expected = initial_data.copy()
        expected.update(update_data)
        assert result == expected
        
        # Context should have merged data
        assert await context.get_data() == expected

    @given(
        bot_id=st.integers(min_value=1, max_value=2**31-1),
        chat_id=st.integers(min_value=-2**63, max_value=2**63-1),
        user_id=st.integers(min_value=1, max_value=2**31-1),
        data=valid_data_strategy,
        key_to_get=st.text(min_size=1, max_size=50),
        default_value=st.one_of(st.none(), st.integers(), st.text())
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_context_get_value(self, bot_id: int, chat_id: int, user_id: int,
                                     data: Dict[str, Any], key_to_get: str,
                                     default_value: Any):
        """Property: FSMContext.get_value should return correct values with defaults"""
        storage_key = StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
        context, storage = create_mock_fsm_context(storage_key)
        
        # Set data
        await context.set_data(data)
        
        if key_to_get in data:
            # Should return the actual value
            value = await context.get_value(key_to_get, default_value)
            assert value == data[key_to_get]
        else:
            # Should return default
            value = await context.get_value(key_to_get, default_value)
            assert value == default_value

    @given(
        bot_id=st.integers(min_value=1, max_value=2**31-1),
        chat_id=st.integers(min_value=-2**63, max_value=2**63-1),
        user_id=st.integers(min_value=1, max_value=2**31-1),
        state_str=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_context_state_management(self, bot_id: int, chat_id: int, 
                                           user_id: int, state_str: str):
        """Property: FSMContext should correctly manage states"""
        key = StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
        context, storage = create_mock_fsm_context(key)
        
        # Set state through context
        await context.set_state(state_str)
        
        # Get state back
        retrieved = await context.get_state()
        assert retrieved == state_str
        
        # Clear state
        await context.set_state(None)
        assert await context.get_state() is None

    @given(
        bot_id=st.integers(min_value=1, max_value=2**31-1),
        chat_id=st.integers(min_value=-2**63, max_value=2**63-1),
        user_id=st.integers(min_value=1, max_value=2**31-1),
        data=valid_data_strategy,
        state=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_context_clear(self, bot_id: int, chat_id: int, user_id: int,
                                 data: Dict[str, Any], state: str):
        """Property: FSMContext.clear should reset both state and data"""
        key = StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
        context, storage = create_mock_fsm_context(key)
        
        # Set state and data
        await context.set_state(state)
        await context.set_data(data)
        
        # Verify they're set
        assert await context.get_state() == state
        assert await context.get_data() == data
        
        # Clear everything
        await context.clear()
        
        # Both should be reset
        assert await context.get_state() is None
        assert await context.get_data() == {}

    @given(
        bot_id=st.integers(min_value=1, max_value=2**31-1),
        chat_id=st.integers(min_value=-2**63, max_value=2**63-1),
        user_id=st.integers(min_value=1, max_value=2**31-1),
        dict_data=valid_data_strategy,
        kwargs_keys=st.lists(
            st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()),
            min_size=1,
            max_size=5,
            unique=True
        ),
        kwargs_values=st.lists(
            st.one_of(st.integers(), st.text(max_size=50)),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_context_update_with_kwargs(self, bot_id: int, chat_id: int, user_id: int,
                                              dict_data: Dict[str, Any],
                                              kwargs_keys: list, kwargs_values: list):
        """Property: FSMContext.update_data should accept both dict and kwargs"""
        key = StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
        context, storage = create_mock_fsm_context(key)
        
        # Make kwargs dict
        kwargs = dict(zip(kwargs_keys[:len(kwargs_values)], 
                         kwargs_values[:len(kwargs_keys)]))
        
        # Set initial data
        await context.set_data({'initial': 'data'})
        
        # Update with both dict and kwargs
        result = await context.update_data(dict_data, **kwargs)
        
        # Should have all updates
        expected = {'initial': 'data'}
        expected.update(dict_data)
        expected.update(kwargs)
        
        assert result == expected
        assert await context.get_data() == expected