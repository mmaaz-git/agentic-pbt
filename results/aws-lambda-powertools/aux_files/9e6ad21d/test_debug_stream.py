#!/usr/bin/env python3
import sys
import os
import io

sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import aws_lambda_powertools.package_logger as package_logger
from aws_lambda_powertools.shared import constants

# Test with debug enabled
os.environ[constants.POWERTOOLS_DEBUG_ENV] = "1"

# Create a custom stream to test
custom_stream = io.StringIO()

print("Testing stream passthrough with debug enabled...")
package_logger.set_package_logger_handler(stream=custom_stream)

# Check if the logger was properly configured 
import logging
logger = logging.getLogger("aws_lambda_powertools")

print(f"Number of handlers: {len(logger.handlers)}")
for handler in logger.handlers:
    print(f"  Handler type: {type(handler).__name__}")
    if hasattr(handler, 'stream'):
        print(f"  Stream: {handler.stream}")
        print(f"  Is custom stream? {handler.stream is custom_stream}")