#!/usr/bin/env python3

import sys
import os

# Add the aiohttp-retry environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

# Now run the tests
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(['test_aiohttp_retry_properties.py', '-v', '--tb=short']))