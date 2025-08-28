#!/usr/bin/env python3
"""Minimal reproduction of the null byte bug in pdfkit.configuration"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.configuration import Configuration

# Test case that causes ValueError instead of IOError
try:
    config = Configuration(wkhtmltopdf=b'\x00')
    print("Configuration created successfully (unexpected)")
except IOError as e:
    print(f"IOError raised as expected: {e}")
except ValueError as e:
    print(f"ValueError raised (BUG!): {e}")
    print("Expected IOError but got ValueError instead")

# Another test case with embedded null byte
try:
    config = Configuration(wkhtmltopdf=b'test\x00path')
    print("Configuration created successfully (unexpected)")
except IOError as e:
    print(f"IOError raised as expected: {e}")
except ValueError as e:
    print(f"ValueError raised (BUG!): {e}")
    print("Expected IOError but got ValueError instead")