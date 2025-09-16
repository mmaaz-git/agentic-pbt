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
)
from langchain_core.messages.ai import UsageMetadata, subtract_usage
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ChatMessage,
)


# Test 1: _create_usage_metadata invariant - Check if it returns correct type
@given(
    prompt_tokens=st.integers(min_value=0, max_value=1_000_000),
    completion_tokens=st.integers(min_value=0, max_value=1_000_000),
)
def test_create_usage_metadata_type_and_invariant(prompt_tokens, completion_tokens):
    """Test that _create_usage_metadata returns UsageMetadata with correct invariant."""
    # Test without total_tokens
    token_usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    result = _create_usage_metadata(token_usage)
    
    # Check if result is UsageMetadata instance
    assert isinstance(result, UsageMetadata), f"Expected UsageMetadata, got {type(result)}"
    
    # The invariant from the code: total = input + output
    assert result.input_tokens == prompt_tokens
    assert result.output_tokens == completion_tokens
    assert result.total_tokens == prompt_tokens + completion_tokens


# Let's also check the actual implementation of _create_usage_metadata
def test_investigate_create_usage_metadata():
    """Investigate the actual return type of _create_usage_metadata."""
    token_usage = {
        "prompt_tokens": 10,
        "completion_tokens": 20,
    }
    result = _create_usage_metadata(token_usage)
    print(f"Type of result: {type(result)}")
    print(f"Result value: {result}")
    
    # Check if it's a dict (which the test failure suggests)
    if isinstance(result, dict):
        print("ERROR: _create_usage_metadata returns dict instead of UsageMetadata!")
        # Check the dict structure
        print(f"Dict keys: {result.keys()}")
        print(f"Dict values: {result}")
        
        # Check if the dict at least has the correct values
        assert result.get("input_tokens") == 10
        assert result.get("output_tokens") == 20
        # Check the invariant
        expected_total = 10 + 20
        actual_total = result.get("total_tokens")
        if actual_total != expected_total:
            print(f"BUG FOUND: total_tokens={actual_total}, expected={expected_total}")
    elif isinstance(result, UsageMetadata):
        print("Correct: Returns UsageMetadata instance")
        assert result.input_tokens == 10
        assert result.output_tokens == 20
        assert result.total_tokens == 30


# Test subtract_usage function
@given(
    total_input=st.integers(min_value=0, max_value=1_000_000),
    total_output=st.integers(min_value=0, max_value=1_000_000),
    prev_input=st.integers(min_value=0, max_value=1_000_000),
    prev_output=st.integers(min_value=0, max_value=1_000_000),
)
def test_usage_metadata_subtraction_type(total_input, total_output, prev_input, prev_output):
    """Test usage metadata subtraction returns correct type and values."""
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
    
    # Check type
    assert isinstance(delta, (UsageMetadata, dict)), f"Unexpected type: {type(delta)}"
    
    if isinstance(delta, dict):
        # If it's a dict, check structure
        assert delta.get("input_tokens") == total_input - prev_input
        assert delta.get("output_tokens") == total_output - prev_output
        expected_total = (total_input + total_output) - (prev_input + prev_output)
        actual_total = delta.get("total_tokens")
        # Check invariant
        assert actual_total == expected_total, f"total_tokens invariant violated: {actual_total} != {expected_total}"
        assert actual_total == delta.get("input_tokens") + delta.get("output_tokens")
    else:
        # If it's UsageMetadata
        assert delta.input_tokens == total_input - prev_input
        assert delta.output_tokens == total_output - prev_output
        assert delta.total_tokens == (total_input + total_output) - (prev_input + prev_output)
        assert delta.total_tokens == delta.input_tokens + delta.output_tokens


# Test with_structured_output with proper schema
from pydantic import BaseModel

class SimpleSchema(BaseModel):
    name: str
    age: int

@given(
    method=st.sampled_from(["json_schema", "function_calling", "json_mode"]),
)
def test_with_structured_output_pydantic_schema(method):
    """Test that with_structured_output works with Pydantic schema."""
    try:
        import os
        os.environ["PPLX_API_KEY"] = "test_key"
        chat = ChatPerplexity()
        
        # Use a Pydantic model as schema (which is what the code expects)
        if method in ["function_calling", "json_mode", "json_schema"]:
            # All should work or fallback to json_schema
            result = chat.with_structured_output(schema=SimpleSchema, method=method)
            assert result is not None
    except Exception as e:
        # Skip if initialization fails due to environment issues
        if "PPLX_API_KEY" in str(e) or "api_key" in str(e) or "openai" in str(e):
            pytest.skip(f"API/environment issue: {e}")
        raise


if __name__ == "__main__":
    # First run the investigation
    print("=" * 50)
    print("INVESTIGATING _create_usage_metadata")
    print("=" * 50)
    test_investigate_create_usage_metadata()
    print()
    
    # Then run the property tests
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short", "-k", "not investigate"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)