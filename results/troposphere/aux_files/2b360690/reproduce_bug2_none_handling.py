#!/usr/bin/env python3
"""Minimal reproduction of bug in validate_document_content with None value"""

import troposphere.validators.ssm as ssm_validators

print("Testing validate_document_content with None value")

try:
    result = ssm_validators.validate_document_content(None)
    print(f"Result: {result}")
except Exception as e:
    print(f"Exception raised: {type(e).__name__}: {e}")
    print("\nExpected behavior: Should raise ValueError with message 'Content must be one of dict or json/yaml string'")
    print("Actual behavior: Raises TypeError from json.loads()")
    
    # Show the bug
    import traceback
    traceback.print_exc()