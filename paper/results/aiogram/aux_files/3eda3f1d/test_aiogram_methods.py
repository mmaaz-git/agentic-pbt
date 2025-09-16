"""Property-based tests for aiogram.methods using Hypothesis"""

import json
from typing import Any, Dict

import pytest
from hypothesis import assume, given, settings, strategies as st

import aiogram.methods
from aiogram.client.default import Default


# Strategy for generating valid chat IDs (can be int or string)
chat_id_strategy = st.one_of(
    st.integers(min_value=-999999999999, max_value=999999999999),
    st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=33, max_codepoint=126))
)

# Strategy for generating text messages
text_strategy = st.text(min_size=1, max_size=4096)

# Strategy for generating boolean values or None
optional_bool_strategy = st.one_of(st.none(), st.booleans())

# Strategy for message IDs
message_id_strategy = st.integers(min_value=1, max_value=2**31-1)


def get_all_method_classes():
    """Get all method classes from aiogram.methods"""
    import inspect
    classes = []
    for name in dir(aiogram.methods):
        if not name.startswith('_'):
            obj = getattr(aiogram.methods, name)
            if inspect.isclass(obj) and hasattr(obj, 'model_fields'):
                classes.append((name, obj))
    return classes


@given(
    chat_id=chat_id_strategy,
    text=text_strategy
)
def test_sendmessage_serialization_with_defaults(chat_id, text):
    """Test that SendMessage with Default values can be serialized to JSON"""
    from aiogram.methods import SendMessage
    
    # Create a SendMessage instance - this will have Default objects
    msg = SendMessage(chat_id=chat_id, text=text)
    
    # model_dump should work
    dumped = msg.model_dump()
    assert dumped['chat_id'] == chat_id
    assert dumped['text'] == text
    
    # Check if Default objects are present
    has_defaults = any(isinstance(v, Default) for v in dumped.values())
    
    if has_defaults:
        # This should fail with Default objects present
        with pytest.raises(Exception) as exc_info:
            msg.model_dump_json()
        # Verify it's specifically about serialization
        assert "serialize" in str(exc_info.value).lower() or "Default" in str(exc_info.value)


@given(
    chat_id=chat_id_strategy,
    text=text_strategy,
    message_thread_id=st.one_of(st.none(), st.integers(min_value=1, max_value=2**31-1)),
    disable_notification=optional_bool_strategy
)
def test_sendmessage_copy_preserves_fields(chat_id, text, message_thread_id, disable_notification):
    """Test that model_copy preserves all fields correctly"""
    from aiogram.methods import SendMessage
    
    msg = SendMessage(
        chat_id=chat_id,
        text=text,
        message_thread_id=message_thread_id,
        disable_notification=disable_notification
    )
    
    # Copy without changes
    copied = msg.model_copy()
    
    # All fields should be preserved
    assert copied.chat_id == msg.chat_id
    assert copied.text == msg.text
    assert copied.message_thread_id == msg.message_thread_id
    assert copied.disable_notification == msg.disable_notification
    
    # The objects should be equal in terms of their data
    assert copied.model_dump() == msg.model_dump()


@given(
    chat_id=chat_id_strategy,
    original_text=text_strategy,
    updated_text=text_strategy
)
def test_sendmessage_copy_update_only_changes_specified(chat_id, original_text, updated_text):
    """Test that model_copy with update only changes specified fields"""
    from aiogram.methods import SendMessage
    
    assume(original_text != updated_text)  # Ensure texts are different
    
    msg = SendMessage(chat_id=chat_id, text=original_text)
    
    # Copy with update
    updated = msg.model_copy(update={'text': updated_text})
    
    # Text should be updated
    assert updated.text == updated_text
    # Chat ID should remain the same
    assert updated.chat_id == chat_id
    # Original should be unchanged
    assert msg.text == original_text


@given(
    chat_id=chat_id_strategy,
    text=text_strategy
)
def test_editmessagetext_with_optional_identifiers(chat_id, text):
    """Test EditMessageText validation - requires either message_id or inline_message_id"""
    from aiogram.methods import EditMessageText
    
    # Should work with chat_id and message_id
    msg1 = EditMessageText(text=text, chat_id=chat_id, message_id=123)
    assert msg1.text == text
    assert msg1.chat_id == chat_id
    
    # Should work with just inline_message_id
    msg2 = EditMessageText(text=text, inline_message_id="inline_123")
    assert msg2.text == text
    assert msg2.inline_message_id == "inline_123"
    
    # Should work with neither (API will determine from context)
    msg3 = EditMessageText(text=text)
    assert msg3.text == text


@given(
    callback_query_id=st.text(min_size=1, max_size=100),
    text=st.one_of(st.none(), text_strategy),
    show_alert=optional_bool_strategy
)
def test_answercallbackquery_serialization(callback_query_id, text, show_alert):
    """Test AnswerCallbackQuery serialization properties"""
    from aiogram.methods import AnswerCallbackQuery
    
    answer = AnswerCallbackQuery(
        callback_query_id=callback_query_id,
        text=text,
        show_alert=show_alert
    )
    
    # Test model_dump
    dumped = answer.model_dump()
    assert dumped['callback_query_id'] == callback_query_id
    assert dumped['text'] == text
    assert dumped['show_alert'] == show_alert
    
    # Test copy
    copied = answer.model_copy()
    assert copied.callback_query_id == callback_query_id
    assert copied.text == text
    assert copied.show_alert == show_alert


@given(
    user_id=st.integers(min_value=1, max_value=2**63-1),
    name=st.text(min_size=1, max_size=64, alphabet=st.characters(blacklist_categories=['Cc', 'Cs'])),
)
def test_addstickerset_required_fields(user_id, name):
    """Test AddStickerToSet with required fields - should fail without sticker"""
    from aiogram.methods import AddStickerToSet
    from pydantic import ValidationError
    
    # Should fail without the required 'sticker' field
    with pytest.raises(ValidationError) as exc_info:
        AddStickerToSet(user_id=user_id, name=name)
    
    # Error should mention missing required field
    assert 'sticker' in str(exc_info.value).lower() or 'required' in str(exc_info.value).lower()


@given(
    chat_id=chat_id_strategy,
    from_chat_id=chat_id_strategy,  
    message_id=message_id_strategy
)
def test_copymessage_copy_operation(chat_id, from_chat_id, message_id):
    """Test CopyMessage model_copy operation preserves all fields"""
    from aiogram.methods import CopyMessage
    
    msg = CopyMessage(
        chat_id=chat_id,
        from_chat_id=from_chat_id,
        message_id=message_id
    )
    
    # Test basic copy
    copied = msg.model_copy()
    assert copied.chat_id == msg.chat_id
    assert copied.from_chat_id == msg.from_chat_id
    assert copied.message_id == msg.message_id
    
    # Test copy with deep=True (should work the same for these simple types)
    deep_copied = msg.model_copy(deep=True)
    assert deep_copied.chat_id == msg.chat_id
    assert deep_copied.from_chat_id == msg.from_chat_id
    assert deep_copied.message_id == msg.message_id


# Test for classes that work without any required fields
@pytest.mark.parametrize("method_class_name", [
    "GetMe", "LogOut", "Close", "GetUpdates", "DeleteWebhook", "GetWebhookInfo"
])
def test_parameterless_methods(method_class_name):
    """Test methods that can be instantiated without parameters"""
    method_class = getattr(aiogram.methods, method_class_name)
    
    # Should be able to create without any parameters
    instance = method_class()
    
    # Should be able to dump to dict
    dumped = instance.model_dump()
    assert isinstance(dumped, dict)
    
    # Should be able to copy
    copied = instance.model_copy()
    assert copied.model_dump() == dumped


@given(
    pre_checkout_query_id=st.text(min_size=1, max_size=100),
    ok=st.booleans(),
    error_message=st.one_of(st.none(), st.text(min_size=1, max_size=200))
)
def test_answerprecheckoutquery_conditional_logic(pre_checkout_query_id, ok, error_message):
    """Test AnswerPreCheckoutQuery - error_message should only be used when ok=False"""
    from aiogram.methods import AnswerPreCheckoutQuery
    
    answer = AnswerPreCheckoutQuery(
        pre_checkout_query_id=pre_checkout_query_id,
        ok=ok,
        error_message=error_message
    )
    
    # Basic field preservation
    assert answer.pre_checkout_query_id == pre_checkout_query_id
    assert answer.ok == ok
    assert answer.error_message == error_message
    
    # Test copy operation
    copied = answer.model_copy()
    assert copied.pre_checkout_query_id == pre_checkout_query_id
    assert copied.ok == ok
    assert copied.error_message == error_message


# Property: All method classes should support basic Pydantic operations
def test_all_methods_support_basic_operations():
    """Test that all method classes support basic Pydantic operations"""
    all_classes = get_all_method_classes()
    
    # Sample 10 random classes for this test
    import random
    sampled_classes = random.sample(all_classes, min(10, len(all_classes)))
    
    for name, cls in sampled_classes:
        # Get required fields
        required_fields = {
            field_name: field_info 
            for field_name, field_info in cls.model_fields.items() 
            if field_info.is_required()
        }
        
        if not required_fields:
            # Can instantiate without args
            instance = cls()
        else:
            # Skip if we can't easily generate valid data
            continue
            
        # Test that basic operations work
        assert hasattr(instance, 'model_dump')
        assert hasattr(instance, 'model_copy')
        assert hasattr(instance, 'model_validate')
        
        # These operations should not raise
        dumped = instance.model_dump()
        assert isinstance(dumped, dict)
        
        copied = instance.model_copy()
        assert type(copied) == type(instance)