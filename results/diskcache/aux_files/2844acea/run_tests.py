#!/usr/bin/env python3
"""Run the property-based tests for diskcache."""

import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

# Import and run the tests
import pytest

# Run pytest programmatically
exit_code = pytest.main(['-v', 'test_diskcache_properties.py'])
sys.exit(exit_code)