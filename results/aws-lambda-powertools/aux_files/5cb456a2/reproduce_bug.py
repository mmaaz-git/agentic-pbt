"""Minimal reproduction of the ModuleNotFoundError bug in middleware_factory"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

# Create a simple middleware with trace_execution=True
@lambda_handler_decorator(trace_execution=True)
def simple_middleware(handler, event, context):
    return handler(event, context)

# Apply the middleware to a handler
@simple_middleware
def lambda_handler(event, context):
    return {"statusCode": 200, "body": "Hello"}

# Try to invoke the handler
try:
    result = lambda_handler({}, {})
    print(f"Success: {result}")
except ModuleNotFoundError as e:
    print(f"BUG FOUND: {e}")
    print(f"Error occurs when trace_execution=True but aws_xray_sdk is not installed")