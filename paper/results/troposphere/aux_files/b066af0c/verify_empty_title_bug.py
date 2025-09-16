#!/usr/bin/env python3
"""Minimal reproduction of the empty title validation bypass bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iot as iot

# The bug: Empty string title bypasses validation
cert = iot.Certificate(title="", Status="ACTIVE")
print(f"Created Certificate with empty title: '{cert.title}'")

# This should have raised ValueError but doesn't
# The validation regex ^[a-zA-Z0-9]+$ doesn't match empty string
# but validate_title() is never called for empty titles