#!/usr/bin/env python3
"""Run tests with more examples to increase confidence."""

import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

# Now import and run the tests with increased examples
import pytest

if __name__ == "__main__":
    # Run with more examples and slower deadline
    sys.exit(pytest.main([
        'test_fire_completion_properties.py', 
        '-v', 
        '--tb=short',
        '--hypothesis-show-statistics'
    ]))