#!/usr/bin/env python3
"""Run the property-based tests for troposphere.iam"""

import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now run pytest
import pytest

if __name__ == "__main__":
    # Run pytest on our test file
    sys.exit(pytest.main(["-v", "test_iam_properties.py"]))