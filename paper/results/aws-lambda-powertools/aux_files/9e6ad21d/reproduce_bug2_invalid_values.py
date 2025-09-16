#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import aws_lambda_powertools.package_logger as package_logger
from aws_lambda_powertools.shared import constants

# Test invalid values that should be treated as False but cause crashes
invalid_values = ["2", "invalid", "maybe", "", "null", "None"]

for value in invalid_values:
    print(f"\nTesting with POWERTOOLS_DEBUG='{value}'")
    os.environ[constants.POWERTOOLS_DEBUG_ENV] = value
    
    try:
        package_logger.set_package_logger_handler()
        print(f"  ✓ Handled gracefully (treated as False)")
    except ValueError as e:
        print(f"  ✗ CRASH: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")