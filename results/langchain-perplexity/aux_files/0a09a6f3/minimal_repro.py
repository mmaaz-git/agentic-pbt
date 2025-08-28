"""Minimal reproduction of the bug in line 279."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/langchain-perplexity_env/lib/python3.13/site-packages')

import os
os.environ["PPLX_API_KEY"] = "test_key"

from langchain_perplexity.chat_models import ChatPerplexity
from langchain_core.messages import ChatMessageChunk

# Create ChatPerplexity instance
chat = ChatPerplexity()

# This triggers the bug: when role=False and default_class=ChatMessageChunk
# Line 279 evaluates: False or True = True (enters the branch)
# Then tries to create ChatMessageChunk(role=False) which fails
delta = {"content": "test message", "role": False}
result = chat._convert_delta_to_message_chunk(delta, ChatMessageChunk)