#!/usr/bin/env python3
"""Run the property-based tests with more examples."""

import sys
import os

# Add the fire package path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

# Change to the working directory
os.chdir('/root/hypothesis-llm/worker_/17')

# Now import and run pytest
import pytest

# Run the tests with hypothesis settings for more examples
sys.exit(pytest.main([
    'test_custom_descriptions_properties.py', 
    '-v', 
    '--tb=short',
    '--hypothesis-show-statistics'
]))