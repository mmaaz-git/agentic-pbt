#!/usr/bin/env python3
"""Run the cloudformation property tests."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now run the tests
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", "test_cloudformation_properties.py"]))