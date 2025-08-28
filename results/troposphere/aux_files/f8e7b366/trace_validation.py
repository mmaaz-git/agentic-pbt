#!/usr/bin/env python3
"""Trace the validation flow"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.mwaa as mwaa

# Monkey-patch to trace calls
original_validate_title = mwaa.Environment.validate_title

def traced_validate_title(self):
    print(f"validate_title called with title={repr(self.title)}")
    try:
        result = original_validate_title(self)
        print(f"  validate_title returned normally")
        return result
    except Exception as e:
        print(f"  validate_title raised: {e}")
        raise

mwaa.Environment.validate_title = traced_validate_title

print("Creating Environment with empty title:")
try:
    env = mwaa.Environment("")
    print(f"SUCCESS: Created with title={repr(env.title)}")
except Exception as e:
    print(f"FAILED: {e}")

print("\nCreating Environment with None title:")
try:
    env = mwaa.Environment(None)
    print(f"SUCCESS: Created with title={repr(env.title)}")
except Exception as e:
    print(f"FAILED: {e}")