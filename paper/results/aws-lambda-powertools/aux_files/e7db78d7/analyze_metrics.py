#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import aws_lambda_powertools.metrics
print('Module imported successfully')
print(f"Module location: {aws_lambda_powertools.metrics.__file__}")