#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere
import troposphere.panorama as panorama

# Let's explore the base classes
print("=== Exploring BaseAWSObject ===")
BaseAWSObject = panorama.AWSObject.__bases__[0]
print(f"BaseAWSObject: {BaseAWSObject}")
print(f"BaseAWSObject methods: {[m for m in dir(BaseAWSObject) if not m.startswith('_')]}")

# Let's look at the boolean validator
print("\n=== Exploring boolean validator ===")
print(f"boolean function signature: {inspect.signature(panorama.boolean)}")
try:
    source = inspect.getsource(panorama.boolean)
    print(f"boolean source:\n{source}")
except:
    print("Could not get source for boolean")

# Let's check the validators module
print("\n=== Checking validators module ===")
from troposphere import validators
print(f"validators.boolean: {validators.boolean}")
print(f"validators.boolean signature: {inspect.signature(validators.boolean)}")
try:
    source = inspect.getsource(validators.boolean)
    print(f"validators.boolean source:\n{source}")
except:
    print("Could not get source")

# Let's look at the to_dict and from_dict methods
print("\n=== Exploring to_dict/from_dict ===")
app_instance = panorama.ApplicationInstance("TestInstance")
print(f"ApplicationInstance.__init__ signature: {inspect.signature(panorama.ApplicationInstance.__init__)}")

# Check the imports in the main troposphere module
print("\n=== Troposphere main module info ===")
print(f"troposphere.__file__: {troposphere.__file__}")
print(f"troposphere.Tags: {troposphere.Tags}")