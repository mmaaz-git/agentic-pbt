#!/usr/bin/env python3
import sys
import os
import logging

sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import aws_lambda_powertools.package_logger as package_logger
from aws_lambda_powertools.shared import constants

# Ensure debug is disabled
os.environ[constants.POWERTOOLS_DEBUG_ENV] = "0"

logger = logging.getLogger("aws_lambda_powertools")
logger.handlers.clear()

# First call
package_logger.set_package_logger_handler()
print(f"After first call: {len(logger.handlers)} handlers")

# Second call - should be idempotent but isn't!
package_logger.set_package_logger_handler()
print(f"After second call: {len(logger.handlers)} handlers")

# Third call
package_logger.set_package_logger_handler()
print(f"After third call: {len(logger.handlers)} handlers")

# Show that all handlers are NullHandlers
for i, handler in enumerate(logger.handlers):
    print(f"Handler {i}: {type(handler).__name__}")

print(f"\nExpected: 1 handler (idempotent)")
print(f"Actual: {len(logger.handlers)} handlers (not idempotent!)")