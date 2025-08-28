"""Property-based tests for langchain_perplexity using Hypothesis."""

import sys
sys.path.append('/root/hypothesis-llm/envs/langchain-perplexity_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from langchain_perplexity import ChatPerplexity
from langchain_perplexity.chat_models import _create_usage_metadata, _is_pydantic_class
from langchain_core.messages import (
    AIMessage, HumanMessage, SystemMessage, ChatMessage,
    AIMessageChunk, HumanMessageChunk, SystemMessageChunk, 
    ChatMessageChunk, FunctionMessageChunk, ToolMessageChunk
)
from pydantic import BaseModel, ValidationError
import pytest


@given(
    prompt_tokens=st.integers(min_value=0, max_value=1000000),
    completion_tokens=st.integers(min_value=0, max_value=1000000)
)
def test_usage_metadata_total_tokens_invariant(prompt_tokens, completion_tokens):
    """Test that total_tokens equals prompt_tokens + completion_tokens when not explicitly provided."""
    # Test case 1: When total_tokens is not provided
    token_usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens
    }
    metadata = _create_usage_metadata(token_usage)
    
    # The function should calculate total_tokens as prompt_tokens + completion_tokens
    assert metadata.total_tokens == prompt_tokens + completion_tokens
    assert metadata.input_tokens == prompt_tokens
    assert metadata.output_tokens == completion_tokens


@given(
    prompt_tokens=st.integers(min_value=0, max_value=1000000),
    completion_tokens=st.integers(min_value=0, max_value=1000000),
    explicit_total=st.integers(min_value=0, max_value=2000000)
)
def test_usage_metadata_explicit_total_tokens(prompt_tokens, completion_tokens, explicit_total):
    """Test that explicit total_tokens is preserved."""
    token_usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": explicit_total
    }
    metadata = _create_usage_metadata(token_usage)
    
    # The function should use the explicit total_tokens value
    assert metadata.total_tokens == explicit_total
    assert metadata.input_tokens == prompt_tokens
    assert metadata.output_tokens == completion_tokens


@given(field_name=st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier()))
def test_build_extra_duplicate_field_detection(field_name):
    """Test that build_extra validator detects duplicate field names."""
    # Simulate values passed to the validator with a field in both places
    values = {
        field_name: "value1",
        "model_kwargs": {field_name: "value2"}
    }
    
    # The validator should raise an error for duplicate fields
    with pytest.raises(ValueError) as exc_info:
        ChatPerplexity.build_extra(values)
    
    assert f"Found {field_name} supplied twice" in str(exc_info.value)


@given(
    model=st.text(min_size=1, max_size=20),
    temperature=st.floats(min_value=0.0, max_value=2.0),
    extra_field=st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier() and x not in ['model', 'temperature', 'model_kwargs'])
)
def test_build_extra_transfers_unknown_fields(model, temperature, extra_field):
    """Test that unknown fields are transferred to model_kwargs."""
    values = {
        "model": model,
        "temperature": temperature,
        extra_field: "extra_value"
    }
    
    result = ChatPerplexity.build_extra(values)
    
    # Extra field should be moved to model_kwargs
    assert extra_field not in result
    assert "model_kwargs" in result
    assert result["model_kwargs"][extra_field] == "extra_value"
    # Known fields should remain
    assert result["model"] == model
    assert result["temperature"] == temperature


def test_with_structured_output_requires_schema():
    """Test that with_structured_output raises error when schema is None."""
    chat = ChatPerplexity(pplx_api_key="test_key")
    
    with pytest.raises(ValueError) as exc_info:
        chat.with_structured_output(schema=None)
    
    assert "schema must be specified" in str(exc_info.value)


@given(
    role=st.sampled_from(["user", "assistant", "system", "function", "tool", None]),
    content=st.text(max_size=100)
)
def test_convert_delta_to_message_chunk_role_mapping(role, content):
    """Test that roles are correctly mapped to message chunk types."""
    chat = ChatPerplexity(pplx_api_key="test_key")
    
    _dict = {"role": role, "content": content}
    
    # Add required fields for function and tool roles
    if role == "function":
        _dict["name"] = "test_function"
    elif role == "tool":
        _dict["tool_call_id"] = "test_tool_id"
    
    # Test the conversion
    result = chat._convert_delta_to_message_chunk(_dict, AIMessageChunk)
    
    # Verify the correct chunk type is returned based on role
    if role == "user":
        assert isinstance(result, HumanMessageChunk)
    elif role == "assistant":
        assert isinstance(result, AIMessageChunk)
    elif role == "system":
        assert isinstance(result, SystemMessageChunk)
    elif role == "function":
        assert isinstance(result, FunctionMessageChunk)
    elif role == "tool":
        assert isinstance(result, ToolMessageChunk)
    elif role is None:
        assert isinstance(result, AIMessageChunk)  # Uses default_class
    
    # Content should be preserved
    assert result.content == content


@given(
    message_type=st.sampled_from([SystemMessage, HumanMessage, AIMessage, ChatMessage]),
    content=st.text(min_size=1, max_size=100)
)
def test_convert_message_to_dict_preserves_content(message_type, content):
    """Test that message content is preserved when converting to dict."""
    chat = ChatPerplexity(pplx_api_key="test_key")
    
    # Create message based on type
    if message_type == ChatMessage:
        message = message_type(content=content, role="custom")
    else:
        message = message_type(content=content)
    
    # Convert to dict
    result = chat._convert_message_to_dict(message)
    
    # Content should be preserved
    assert result["content"] == content
    
    # Role should be set correctly
    if isinstance(message, SystemMessage):
        assert result["role"] == "system"
    elif isinstance(message, HumanMessage):
        assert result["role"] == "user"
    elif isinstance(message, AIMessage):
        assert result["role"] == "assistant"
    elif isinstance(message, ChatMessage):
        assert result["role"] == "custom"


class TestModel(BaseModel):
    """Test model for pydantic class detection."""
    field: str


@given(obj=st.one_of(
    st.just(TestModel),  # Pydantic class
    st.just(dict),  # Non-pydantic class
    st.just(str),  # Built-in type
    st.just(42),  # Non-class object
    st.just(TestModel(field="test")),  # Pydantic instance
))
def test_is_pydantic_class_detection(obj):
    """Test that _is_pydantic_class correctly identifies Pydantic classes."""
    result = _is_pydantic_class(obj)
    
    # Only TestModel class should return True
    if obj is TestModel:
        assert result is True
    else:
        assert result is False