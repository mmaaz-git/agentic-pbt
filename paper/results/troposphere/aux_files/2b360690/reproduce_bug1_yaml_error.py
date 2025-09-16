#!/usr/bin/env python3
"""Minimal reproduction of bug in validate_document_content with special characters"""

import troposphere.validators.ssm as ssm_validators

# This character causes yaml.reader.ReaderError
special_char = '\x1f'

print(f"Testing validate_document_content with special character: {repr(special_char)}")

try:
    result = ssm_validators.validate_document_content(special_char)
    print(f"Result: {result}")
except Exception as e:
    print(f"Exception raised: {type(e).__name__}: {e}")
    print("\nExpected behavior: Should raise ValueError with message 'Content must be one of dict or json/yaml string'")
    print("Actual behavior: Raises yaml.reader.ReaderError instead")
    
    # Show the bug
    import traceback
    traceback.print_exc()