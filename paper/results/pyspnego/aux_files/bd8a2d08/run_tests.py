#!/usr/bin/env python3
"""Run the property-based tests for spnego.negotiate."""

import sys
import subprocess

# Add the virtual environment site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

# Now run pytest programmatically
import pytest

# Run the tests
sys.exit(pytest.main([
    'test_spnego_negotiate_properties.py',
    '-v',
    '--tb=short',
    '--hypothesis-show-statistics'
]))