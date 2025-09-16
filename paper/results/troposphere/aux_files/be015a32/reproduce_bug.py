#!/usr/bin/env python
"""Minimal reproduction of the string formatting bug in troposphere.glue validators"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.glue import connection_type_validator

# This will raise TypeError instead of ValueError with a proper error message
connection_type_validator("INVALID")