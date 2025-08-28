#!/usr/bin/env python3
import sys
import os

# Add site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

# Import and run pytest
import pytest

# Run the tests
sys.exit(pytest.main(['test_sqltrie_properties.py', '-v', '--tb=short']))