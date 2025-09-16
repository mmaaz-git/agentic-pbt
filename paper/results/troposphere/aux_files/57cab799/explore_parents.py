#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
import troposphere.validators as validators
import inspect

print("=== AWSObject source ===")
print(inspect.getsource(troposphere.AWSObject))

print("\n=== AWSProperty source ===")
print(inspect.getsource(troposphere.AWSProperty))

print("\n=== double function ===")
print(f"Location: {inspect.getfile(validators.double)}")
print(f"Signature: {inspect.signature(validators.double)}")
print("Source:")
print(inspect.getsource(validators.double))