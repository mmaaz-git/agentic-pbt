# Bug Report: langchain_perplexity Message Role to Chunk Type Mapping Logic Error

**Target**: `langchain_perplexity.chat_models.ChatPerplexity._convert_delta_to_message_chunk`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_convert_delta_to_message_chunk` method incorrectly uses `or` operators instead of proper precedence logic when determining message chunk types, causing it to ignore the role parameter when certain default_class values are provided.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from langchain_perplexity import ChatPerplexity
from langchain_core.messages import (
    AIMessageChunk, SystemMessageChunk, FunctionMessageChunk, ToolMessageChunk
)

@given(
    role=st.sampled_from(["system", "function", "tool"]),
    content=st.text(max_size=100)
)
def test_convert_delta_to_message_chunk_role_mapping(role, content):
    chat = ChatPerplexity(pplx_api_key="test_key")
    
    _dict = {"role": role, "content": content}
    
    if role == "function":
        _dict["name"] = "test_function"
    elif role == "tool":
        _dict["tool_call_id"] = "test_tool_id"
    
    result = chat._convert_delta_to_message_chunk(_dict, AIMessageChunk)
    
    if role == "system":
        assert isinstance(result, SystemMessageChunk)
    elif role == "function":
        assert isinstance(result, FunctionMessageChunk)
    elif role == "tool":
        assert isinstance(result, ToolMessageChunk)
```

**Failing input**: `role='system', content='', default_class=AIMessageChunk`

## Reproducing the Bug

```python
from langchain_perplexity import ChatPerplexity
from langchain_core.messages import AIMessageChunk

chat = ChatPerplexity(pplx_api_key="test_key")

delta = {"role": "system", "content": "System message"}
result = chat._convert_delta_to_message_chunk(delta, AIMessageChunk)

print(f"Expected: SystemMessageChunk")
print(f"Actual: {type(result).__name__}")
```

## Why This Is A Bug

The method's conditional logic uses `or` operators that cause incorrect precedence evaluation. When `default_class` is `AIMessageChunk`, the condition `role == "assistant" or default_class == AIMessageChunk` evaluates to True regardless of the actual role value, causing all messages to be converted to AIMessageChunk instead of their appropriate types based on role.

This violates the expected behavior where the role should determine the message chunk type when explicitly provided, with default_class only used as a fallback.

## Fix

```diff
--- a/langchain_perplexity/chat_models.py
+++ b/langchain_perplexity/chat_models.py
@@ -266,19 +266,19 @@ class ChatPerplexity(BaseChatModel):
         if _dict.get("tool_calls"):
             additional_kwargs["tool_calls"] = _dict["tool_calls"]
 
-        if role == "user" or default_class == HumanMessageChunk:
+        if role == "user":
             return HumanMessageChunk(content=content)
-        elif role == "assistant" or default_class == AIMessageChunk:
+        elif role == "assistant":
             return AIMessageChunk(content=content, additional_kwargs=additional_kwargs)
-        elif role == "system" or default_class == SystemMessageChunk:
+        elif role == "system":
             return SystemMessageChunk(content=content)
-        elif role == "function" or default_class == FunctionMessageChunk:
+        elif role == "function":
             return FunctionMessageChunk(content=content, name=_dict["name"])
-        elif role == "tool" or default_class == ToolMessageChunk:
+        elif role == "tool":
             return ToolMessageChunk(content=content, tool_call_id=_dict["tool_call_id"])
-        elif role or default_class == ChatMessageChunk:
+        elif role:
             return ChatMessageChunk(content=content, role=role)
         else:
             return default_class(content=content)
```