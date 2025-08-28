"""Test edge cases and find bugs in langchain_perplexity."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/langchain-perplexity_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import pytest
from langchain_perplexity.chat_models import (
    _create_usage_metadata,
    ChatPerplexity,
    _convert_delta_to_message_chunk,
)
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ChatMessage,
    BaseMessage,
)
from langchain_core.messages import (
    AIMessageChunk,
    HumanMessageChunk,
    SystemMessageChunk,
    ChatMessageChunk,
)


# Test 1: _convert_delta_to_message_chunk edge case with role=None
@given(
    content=st.text(min_size=0, max_size=100),
    role=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
)
def test_convert_delta_edge_cases(content, role):
    """Test _convert_delta_to_message_chunk with edge cases."""
    try:
        # Create a minimal ChatPerplexity instance
        import os
        os.environ["PPLX_API_KEY"] = "test_key"
        chat = ChatPerplexity()
        
        # Test with various role values
        delta = {"content": content}
        if role is not None:
            delta["role"] = role
        
        # This should handle None role
        result = chat._convert_delta_to_message_chunk(delta, AIMessageChunk)
        
        # Check result is valid
        assert result is not None
        assert hasattr(result, "content")
        
    except Exception as e:
        if "PPLX_API_KEY" in str(e) or "api_key" in str(e) or "openai" in str(e):
            pytest.skip(f"API/environment issue: {e}")
        # Re-raise to catch real bugs
        raise


# Test 2: Check the logic in line 279 - potential bug with role evaluation
def test_line_279_logic_bug():
    """Test the suspicious logic in line 279."""
    import os
    os.environ["PPLX_API_KEY"] = "test_key"
    chat = ChatPerplexity()
    
    # Line 279: elif role or default_class == ChatMessageChunk:
    # This is suspicious! It should be: elif role and default_class == ChatMessageChunk:
    # or: elif (role) or (default_class == ChatMessageChunk):
    
    # Test case 1: role=None, default_class != ChatMessageChunk
    # The condition will evaluate as: None or False = False (correct)
    delta1 = {"content": "test", "role": None}
    result1 = chat._convert_delta_to_message_chunk(delta1, AIMessageChunk)
    print(f"Test 1 - role=None, default=AIMessageChunk: {type(result1)}")
    
    # Test case 2: role="", default_class != ChatMessageChunk  
    # The condition will evaluate as: "" or False = False (problematic!)
    # Empty string is falsy, so this won't enter the branch
    delta2 = {"content": "test", "role": ""}
    result2 = chat._convert_delta_to_message_chunk(delta2, AIMessageChunk)
    print(f"Test 2 - role='', default=AIMessageChunk: {type(result2)}")
    
    # Test case 3: role="custom", default_class = HumanMessageChunk
    # The condition will evaluate as: "custom" or False = "custom" (enters branch)
    delta3 = {"content": "test", "role": "custom"}
    result3 = chat._convert_delta_to_message_chunk(delta3, HumanMessageChunk)
    print(f"Test 3 - role='custom', default=HumanMessageChunk: {type(result3)}")
    
    # Test case 4: role=0, default_class != ChatMessageChunk
    # The condition will evaluate as: 0 or False = False (problematic if role can be 0!)
    delta4 = {"content": "test", "role": 0}
    try:
        result4 = chat._convert_delta_to_message_chunk(delta4, AIMessageChunk)
        print(f"Test 4 - role=0, default=AIMessageChunk: {type(result4)}")
    except Exception as e:
        print(f"Test 4 - role=0 caused error: {e}")
    
    # Test case 5: role=False, default_class = ChatMessageChunk
    # The condition will evaluate as: False or True = True (enters branch incorrectly!)
    delta5 = {"content": "test", "role": False}
    try:
        result5 = chat._convert_delta_to_message_chunk(delta5, ChatMessageChunk)
        print(f"Test 5 - role=False, default=ChatMessageChunk: {type(result5)}")
        # This will likely fail because it tries to create ChatMessageChunk with role=False
    except Exception as e:
        print(f"Test 5 - role=False caused error: {e}")


# Test 3: Test message types that are not explicitly handled
class CustomMessage(BaseMessage):
    """Custom message type not handled by the code."""
    def __init__(self, content: str):
        super().__init__(content=content, type="custom")
    
    @property
    def type(self) -> str:
        return "custom"

def test_unhandled_message_type():
    """Test that unhandled message types raise appropriate errors."""
    import os
    os.environ["PPLX_API_KEY"] = "test_key"
    chat = ChatPerplexity()
    
    # This should raise TypeError as per line 241
    custom_msg = CustomMessage(content="test")
    
    try:
        result = chat._convert_message_to_dict(custom_msg)
        print(f"Unexpected success with custom message: {result}")
    except TypeError as e:
        print(f"Expected TypeError: {e}")
        assert "Got unknown type" in str(e)


# Test 4: Test duplicate field names in build_extra
def test_build_extra_edge_cases():
    """Test edge cases in build_extra validator."""
    
    # Test with empty string as field name
    values1 = {
        "": "value1",
        "model_kwargs": {"": "value2"},
    }
    
    try:
        result = ChatPerplexity.build_extra(values1)
        print(f"Empty string field name accepted: {result}")
    except ValueError as e:
        print(f"Empty string field name rejected: {e}")
    
    # Test with special characters in field names
    values2 = {
        "field-name": "value1",
        "model_kwargs": {"field-name": "value2"},
    }
    
    try:
        result = ChatPerplexity.build_extra(values2)
        print(f"Field with hyphen accepted: {result}")
    except ValueError as e:
        print(f"Field with hyphen rejected: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING LINE 279 LOGIC BUG")
    print("=" * 60)
    test_line_279_logic_bug()
    
    print("\n" + "=" * 60)
    print("TESTING UNHANDLED MESSAGE TYPE")
    print("=" * 60)
    test_unhandled_message_type()
    
    print("\n" + "=" * 60)
    print("TESTING BUILD_EXTRA EDGE CASES")
    print("=" * 60)
    test_build_extra_edge_cases()
    
    print("\n" + "=" * 60)
    print("RUNNING HYPOTHESIS TESTS")
    print("=" * 60)
    
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short", "-k", "test_convert_delta"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)