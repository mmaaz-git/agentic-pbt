#!/usr/bin/env python3
"""Simple test runner for property-based tests."""

import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

# Now import and run the tests
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(['test_fire_completion_properties.py', '-v', '--tb=short']))