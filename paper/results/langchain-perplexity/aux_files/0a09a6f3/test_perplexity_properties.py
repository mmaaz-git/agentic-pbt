"""Property-based tests for langchain_perplexity.chat_models using Hypothesis."""

import sys
import os

# Add the package to path
sys.path.insert(0, '/root/hypothesis-llm/envs/langchain-perplexity_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import math
import pytest
from langchain_perplexity.chat_models import (
    _create_usage_metadata,
    ChatPerplexity,
    subtract_usage,
)
from langchain_core.messages.ai import UsageMetadata
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ChatMessage,
)


# Test 1: _create_usage_metadata invariant
# The code explicitly states: total_tokens = input_tokens + output_tokens when total not provided
@given(
    prompt_tokens=st.integers(min_value=0, max_value=1_000_000),
    completion_tokens=st.integers(min_value=0, max_value=1_000_000),
)
def test_create_usage_metadata_invariant(prompt_tokens, completion_tokens):
    """Test that _create_usage_metadata correctly calculates total_tokens."""
    # Test without total_tokens
    token_usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    result = _create_usage_metadata(token_usage)
    
    # The invariant from the code: total = input + output
    assert result.input_tokens == prompt_tokens
    assert result.output_tokens == completion_tokens
    assert result.total_tokens == prompt_tokens + completion_tokens


@given(
    prompt_tokens=st.integers(min_value=0, max_value=1_000_000),
    completion_tokens=st.integers(min_value=0, max_value=1_000_000),
    total_tokens=st.integers(min_value=0, max_value=2_000_000),
)
def test_create_usage_metadata_with_total(prompt_tokens, completion_tokens, total_tokens):
    """Test that _create_usage_metadata respects provided total_tokens."""
    token_usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
    result = _create_usage_metadata(token_usage)
    
    # When total is provided, it should use that value
    assert result.input_tokens == prompt_tokens
    assert result.output_tokens == completion_tokens
    assert result.total_tokens == total_tokens


# Test 2: build_extra duplicate field detection
@given(
    field_name=st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier()),
    value1=st.integers(),
    value2=st.integers(),
)
def test_build_extra_duplicate_detection(field_name, value1, value2):
    """Test that build_extra correctly detects duplicate fields."""
    # Create a scenario where field appears in both values and model_kwargs
    values = {
        field_name: value1,
        "model_kwargs": {field_name: value2},
    }
    
    # The code should raise ValueError for duplicate fields
    with pytest.raises(ValueError, match=f"Found {field_name} supplied twice"):
        ChatPerplexity.build_extra(values)


# Test 3: Message conversion round-trip property
@given(
    content=st.text(min_size=0, max_size=1000),
    role=st.sampled_from(["system", "user", "assistant", "custom"]),
)
def test_message_conversion_consistency(content, role):
    """Test that message conversion maintains role and content correctly."""
    # Create a ChatPerplexity instance with minimal config
    # Note: We need to mock or skip validation since we don't have API key
    try:
        chat = ChatPerplexity(pplx_api_key="test_key")
    except:
        # If initialization fails due to API validation, test the method directly
        # Create a minimal instance for testing
        import os
        os.environ["PPLX_API_KEY"] = "test_key"
        chat = ChatPerplexity()
    
    # Test different message types
    if role == "system":
        message = SystemMessage(content=content)
        result = chat._convert_message_to_dict(message)
        assert result["role"] == "system"
        assert result["content"] == content
    elif role == "user":
        message = HumanMessage(content=content)
        result = chat._convert_message_to_dict(message)
        assert result["role"] == "user"
        assert result["content"] == content
    elif role == "assistant":
        message = AIMessage(content=content)
        result = chat._convert_message_to_dict(message)
        assert result["role"] == "assistant"
        assert result["content"] == content
    elif role == "custom":
        message = ChatMessage(role="custom_role", content=content)
        result = chat._convert_message_to_dict(message)
        assert result["role"] == "custom_role"
        assert result["content"] == content


# Test 4: Usage metadata subtraction non-negative invariant
@given(
    total_input=st.integers(min_value=0, max_value=1_000_000),
    total_output=st.integers(min_value=0, max_value=1_000_000),
    prev_input=st.integers(min_value=0, max_value=1_000_000),
    prev_output=st.integers(min_value=0, max_value=1_000_000),
)
def test_usage_metadata_subtraction(total_input, total_output, prev_input, prev_output):
    """Test usage metadata subtraction in streaming."""
    # Assume totals are cumulative (should be >= previous)
    assume(total_input >= prev_input)
    assume(total_output >= prev_output)
    
    total_usage = UsageMetadata(
        input_tokens=total_input,
        output_tokens=total_output,
        total_tokens=total_input + total_output,
    )
    
    prev_usage = UsageMetadata(
        input_tokens=prev_input,
        output_tokens=prev_output,
        total_tokens=prev_input + prev_output,
    )
    
    # Test the subtraction
    delta = subtract_usage(total_usage, prev_usage)
    
    # Deltas should be non-negative and correct
    assert delta.input_tokens == total_input - prev_input
    assert delta.output_tokens == total_output - prev_output
    assert delta.total_tokens == (total_input + total_output) - (prev_input + prev_output)
    
    # Verify invariant: delta.total = delta.input + delta.output
    assert delta.total_tokens == delta.input_tokens + delta.output_tokens


# Test 5: with_structured_output method parameter handling
@given(
    method=st.sampled_from(["json_schema", "function_calling", "json_mode", "invalid_method"]),
)
def test_with_structured_output_method_handling(method):
    """Test that with_structured_output correctly handles method parameters."""
    try:
        import os
        os.environ["PPLX_API_KEY"] = "test_key"
        chat = ChatPerplexity()
        
        # Create a simple schema
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        
        if method in ["function_calling", "json_mode"]:
            # These should fallback to json_schema without error
            result = chat.with_structured_output(schema=schema, method=method)
            assert result is not None
        elif method == "json_schema":
            # This should work normally
            result = chat.with_structured_output(schema=schema, method=method)
            assert result is not None
        elif method == "invalid_method":
            # This should raise ValueError
            with pytest.raises(ValueError, match="Unrecognized method argument"):
                chat.with_structured_output(schema=schema, method=method)
    except Exception as e:
        # Skip if initialization fails due to environment issues
        if "PPLX_API_KEY" in str(e) or "api_key" in str(e):
            pytest.skip("API key validation failed, skipping test")
        raise


if __name__ == "__main__":
    # Run the tests
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)