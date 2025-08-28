#!/usr/bin/env python3
"""Run the property-based tests."""

import sys
import os

# Add the dagster-pandas environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

# Now run the tests
import pytest
exit_code = pytest.main(['test_dagster_pandas_validation.py', '-v', '--tb=short'])
sys.exit(exit_code)