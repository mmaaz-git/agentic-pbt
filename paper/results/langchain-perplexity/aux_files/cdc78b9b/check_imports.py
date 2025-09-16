"""Check what UsageMetadata actually is."""

import sys
sys.path.append('/root/hypothesis-llm/envs/langchain-perplexity_env/lib/python3.13/site-packages')

from langchain_core.messages.ai import UsageMetadata
print(f"UsageMetadata type: {type(UsageMetadata)}")
print(f"UsageMetadata: {UsageMetadata}")

# Try creating one
usage = UsageMetadata(input_tokens=10, output_tokens=20, total_tokens=30)
print(f"Created usage type: {type(usage)}")
print(f"Created usage: {usage}")
print(f"Has total_tokens attr: {hasattr(usage, 'total_tokens')}")
if hasattr(usage, 'total_tokens'):
    print(f"total_tokens value: {usage.total_tokens}")