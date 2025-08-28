"""Check the actual types and behavior."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/langchain-perplexity_env/lib/python3.13/site-packages')

from langchain_core.messages.ai import UsageMetadata, subtract_usage
from langchain_perplexity.chat_models import _create_usage_metadata
import typing

print("=" * 60)
print("CHECKING UsageMetadata TYPE")
print("=" * 60)
print(f"UsageMetadata type: {type(UsageMetadata)}")
print(f"Is TypedDict: {typing.get_origin(UsageMetadata) is typing.TypedDict or 'TypedDict' in str(type(UsageMetadata))}")

if hasattr(UsageMetadata, '__annotations__'):
    print(f"Annotations: {UsageMetadata.__annotations__}")

# Test _create_usage_metadata
print("\n" + "=" * 60)
print("TESTING _create_usage_metadata")
print("=" * 60)

test_data = {"prompt_tokens": 10, "completion_tokens": 20}
result = _create_usage_metadata(test_data)
print(f"Result type: {type(result)}")
print(f"Result: {result}")

# Check if it matches UsageMetadata structure
if hasattr(UsageMetadata, '__annotations__'):
    expected_keys = set(UsageMetadata.__annotations__.keys())
    actual_keys = set(result.keys())
    print(f"Expected keys: {expected_keys}")
    print(f"Actual keys: {actual_keys}")
    print(f"Keys match: {expected_keys == actual_keys}")

# Test with provided total_tokens
test_data_with_total = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 35}
result_with_total = _create_usage_metadata(test_data_with_total)
print(f"\nWith provided total_tokens=35:")
print(f"Result: {result_with_total}")
print(f"Bug? total_tokens should be 35 but is {result_with_total.get('total_tokens')}")

# Test subtract_usage
print("\n" + "=" * 60)
print("TESTING subtract_usage")
print("=" * 60)

usage1 = {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
usage2 = {"input_tokens": 30, "output_tokens": 20, "total_tokens": 50}

# Create UsageMetadata-like dicts
result_subtract = subtract_usage(usage1, usage2)
print(f"subtract_usage result type: {type(result_subtract)}")
print(f"Result: {result_subtract}")
print(f"Expected: input=70, output=30, total=100")

# Check invariant
if isinstance(result_subtract, dict):
    input_t = result_subtract.get("input_tokens", 0)
    output_t = result_subtract.get("output_tokens", 0)
    total_t = result_subtract.get("total_tokens", 0)
    print(f"Invariant check: {input_t} + {output_t} = {total_t}? {input_t + output_t == total_t}")