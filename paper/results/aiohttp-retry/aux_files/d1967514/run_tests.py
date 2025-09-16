#!/usr/bin/env /root/hypothesis-llm/envs/aiohttp-retry_env/bin/python3
"""Runner for property-based tests."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

import pytest

if __name__ == "__main__":
    # Run the tests with verbose output
    exit_code = pytest.main(["-v", "test_aiohttp_retry_properties.py"])
    sys.exit(exit_code)