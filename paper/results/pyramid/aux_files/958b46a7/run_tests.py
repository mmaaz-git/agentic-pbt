#!/usr/bin/env python
"""Simple test runner that adds the pyramid env to sys.path."""
import sys
import os

# Add the pyramid environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

# Now run the tests
import pytest
sys.exit(pytest.main(['test_pyramid_tweens.py', '-v', '--tb=short']))