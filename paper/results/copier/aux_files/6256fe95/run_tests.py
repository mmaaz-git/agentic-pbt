#!/usr/bin/env python3
"""Run the property-based tests for copier._user_data."""

import sys
import traceback

# Add the copier environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

# Import pytest
import pytest

# Run the tests
if __name__ == "__main__":
    # Run pytest with verbose output
    sys.exit(pytest.main(["-v", "test_copier_user_data.py"]))