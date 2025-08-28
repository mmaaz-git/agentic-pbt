"""Test for the bug in line 279 of chat_models.py."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/langchain-perplexity_env/lib/python3.13/site-packages')

from langchain_perplexity.chat_models import ChatPerplexity
from langchain_core.messages import (
    AIMessageChunk,
    ChatMessageChunk,
)
import os

def test_line_279_logic_bug():
    """Test the bug in line 279: elif role or default_class == ChatMessageChunk."""
    
    os.environ["PPLX_API_KEY"] = "test_key"
    chat = ChatPerplexity()
    
    print("Testing line 279: elif role or default_class == ChatMessageChunk:")
    print("This should be: elif role or (default_class == ChatMessageChunk):")
    print("or: elif (role is not None) or (default_class == ChatMessageChunk):")
    print()
    
    # Bug case: role=False, default_class=ChatMessageChunk
    # The condition evaluates as: False or True = True (enters branch)
    # But then it tries to create ChatMessageChunk with role=False
    print("Test 1: role=False, default_class=ChatMessageChunk")
    delta1 = {"content": "test"}
    delta1["role"] = False  # Explicitly set to False
    
    try:
        result1 = chat._convert_delta_to_message_chunk(delta1, ChatMessageChunk)
        print(f"  Result type: {type(result1)}")
        print(f"  Result role: {result1.role if hasattr(result1, 'role') else 'N/A'}")
        
        # Check if False was incorrectly passed as role
        if hasattr(result1, 'role') and result1.role is False:
            print("  BUG CONFIRMED: False passed as role to ChatMessageChunk!")
    except TypeError as e:
        print(f"  ERROR (likely bug): {e}")
        if "expected string or bytes-like object" in str(e) or "expected str" in str(e):
            print("  BUG CONFIRMED: ChatMessageChunk expects string role, got False!")
    except Exception as e:
        print(f"  Unexpected error: {e}")
    
    print()
    
    # Bug case 2: role=0, should it enter the ChatMessageChunk branch?
    print("Test 2: role=0, default_class=ChatMessageChunk")
    delta2 = {"content": "test", "role": 0}
    
    try:
        result2 = chat._convert_delta_to_message_chunk(delta2, ChatMessageChunk)
        print(f"  Result type: {type(result2)}")
        if hasattr(result2, 'role'):
            print(f"  Result role: {result2.role}")
    except TypeError as e:
        print(f"  ERROR: {e}")
        if "expected string" in str(e).lower() or "expected str" in str(e):
            print("  BUG: Numeric role not handled properly!")
    except Exception as e:
        print(f"  Unexpected error: {e}")
    
    print()
    
    # Bug case 3: Empty list as role (falsy but not None)
    print("Test 3: role=[], default_class=ChatMessageChunk")
    delta3 = {"content": "test", "role": []}
    
    try:
        result3 = chat._convert_delta_to_message_chunk(delta3, ChatMessageChunk)
        print(f"  Result type: {type(result3)}")
        if hasattr(result3, 'role'):
            print(f"  Result role: {result3.role}")
    except TypeError as e:
        print(f"  ERROR: {e}")
        print("  BUG: Empty list as role causes error!")
    except Exception as e:
        print(f"  Unexpected error: {e}")
    
    print()
    
    # Test what happens with None role
    print("Test 4: role=None, default_class=ChatMessageChunk")
    delta4 = {"content": "test", "role": None}
    
    try:
        result4 = chat._convert_delta_to_message_chunk(delta4, ChatMessageChunk)
        print(f"  Result type: {type(result4)}")
        if hasattr(result4, 'role'):
            print(f"  Result role: {result4.role}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Additional problematic case: role="" (empty string is falsy)
    print("Test 5: role='', default_class=AIMessageChunk")
    delta5 = {"content": "test", "role": ""}
    
    result5 = chat._convert_delta_to_message_chunk(delta5, AIMessageChunk)
    print(f"  Result type: {type(result5)}")
    print(f"  Empty string role bypassed ChatMessageChunk logic (may be intended)")


if __name__ == "__main__":
    test_line_279_logic_bug()