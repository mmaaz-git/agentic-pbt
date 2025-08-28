#!/usr/bin/env python3
"""Minimal reproduction of BedrockResponse.is_json() bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.event_handler.api_gateway import BedrockResponse

# Test various content types
content_types = [
    "application/json",  # Should return True
    "text/plain",        # Should return False
    "text/html",         # Should return False
    "application/xml",   # Should return False
    "image/png",         # Should return False
    "video/mp4",         # Should return False
]

print("BedrockResponse.is_json() test results:")
print("-" * 40)

for content_type in content_types:
    response = BedrockResponse(
        body="test content",
        content_type=content_type
    )
    
    result = response.is_json()
    expected = "json" in content_type.lower()
    
    if result == expected:
        print(f"✓ {content_type}: is_json()={result} (correct)")
    else:
        print(f"✗ {content_type}: is_json()={result} (expected {expected})")

print("\nBUG: BedrockResponse.is_json() always returns True regardless of content_type!")