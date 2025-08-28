#!/usr/bin/env python3
"""Reproduce the boolean validator accepting floats bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test that boolean accepts float 0.0 and 1.0
print("Testing boolean validator with floats:")
print(f"boolean(0.0) = {boolean(0.0)}")  # Should raise ValueError but returns False
print(f"boolean(1.0) = {boolean(1.0)}")  # Should raise ValueError but returns True

# The function should only accept:
# True values: True, 1, "1", "true", "True"  
# False values: False, 0, "0", "false", "False"
# But it accepts floats 0.0 and 1.0 as well