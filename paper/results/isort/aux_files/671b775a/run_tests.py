#!/usr/bin/env python3
import sys
import os

# Add the isort environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

# Now import and run the tests
import pytest

# Run pytest with our test file
exit_code = pytest.main(['test_isort_io.py', '-v', '--tb=short'])
sys.exit(exit_code)