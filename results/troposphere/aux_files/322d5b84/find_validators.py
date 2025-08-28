#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators
import inspect

print(f"validators module file: {validators.__file__}")
print(f"\ninteger function source:")
print(inspect.getsource(validators.integer))