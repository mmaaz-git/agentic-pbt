#!/usr/bin/env python
"""Runner script for property-based tests"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import pytest

# Run the tests
sys.exit(pytest.main(['test_finspace.py', '-v', '--tb=short']))