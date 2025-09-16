#!/usr/bin/env python3
"""Minimal reproduction of the Info() bug with objects that have failing __str__ methods."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils

# Create an object with a __str__ that raises an exception
class BadStr:
    def __str__(self):
        raise ValueError("Cannot convert to string!")

# This should crash when Info tries to get string_form
bad_obj = BadStr()
info = inspectutils.Info(bad_obj)
print(f"Info returned: {info}")