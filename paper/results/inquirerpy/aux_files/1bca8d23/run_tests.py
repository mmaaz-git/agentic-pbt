#!/usr/bin/env python3
"""Run the property-based tests for InquirerPy.utils."""

import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

# Import and run the tests
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["test_inquirerpy_utils.py", "-v", "--tb=short"]))