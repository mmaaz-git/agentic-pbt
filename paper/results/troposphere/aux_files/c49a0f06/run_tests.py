#!/usr/bin/env python3
"""Run the property-based tests for troposphere.dax"""

import sys
import os

# Add the troposphere env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now run the tests
import pytest

# Run pytest on our test file
exit_code = pytest.main(['-v', '--tb=short', 'test_troposphere_dax.py'])
sys.exit(exit_code)