"""Minimal reproductions of the bugs found in langchain_perplexity."""

import sys
sys.path.append('/root/hypothesis-llm/envs/langchain-perplexity_env/lib/python3.13/site-packages')

from langchain_perplexity import ChatPerplexity
from langchain_perplexity.chat_models import _create_usage_metadata
from langchain_core.messages import AIMessageChunk

print("Bug 1: _create_usage_metadata returns dict instead of UsageMetadata")
print("="*60)

# Minimal reproduction
token_usage = {"prompt_tokens": 10, "completion_tokens": 20}
result = _create_usage_metadata(token_usage)

print(f"Input: {token_usage}")
print(f"Result type: {type(result)}")
print(f"Result: {result}")

# Try to access attributes as documented
try:
    print(f"Trying to access result.total_tokens...")
    print(f"result.total_tokens = {result.total_tokens}")
except AttributeError as e:
    print(f"ERROR: {e}")

print("\n" + "="*60)
print("Bug 2: _convert_delta_to_message_chunk ignores role when default_class provided")
print("="*60)

chat = ChatPerplexity(pplx_api_key="test_key")

# Test 1: Role is 'system' but default_class is AIMessageChunk
delta1 = {"role": "system", "content": "System message"}
result1 = chat._convert_delta_to_message_chunk(delta1, AIMessageChunk)
print(f"\nInput: role='system', default_class=AIMessageChunk")
print(f"Expected: SystemMessageChunk")
print(f"Actual: {type(result1).__name__}")

# Test 2: Role is 'tool' but default_class is AIMessageChunk  
delta2 = {"role": "tool", "content": "Tool output", "tool_call_id": "123"}
result2 = chat._convert_delta_to_message_chunk(delta2, AIMessageChunk)
print(f"\nInput: role='tool', default_class=AIMessageChunk")
print(f"Expected: ToolMessageChunk")
print(f"Actual: {type(result2).__name__}")

# Test 3: Role is 'function' but default_class is AIMessageChunk
delta3 = {"role": "function", "content": "Function output", "name": "my_func"}
result3 = chat._convert_delta_to_message_chunk(delta3, AIMessageChunk)
print(f"\nInput: role='function', default_class=AIMessageChunk")
print(f"Expected: FunctionMessageChunk")  
print(f"Actual: {type(result3).__name__}")