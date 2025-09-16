#!/usr/bin/env python3
import sys
import os

# Add the troposphere environment's site-packages to the Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now import and run pytest
import pytest

# Run pytest on our test file
sys.exit(pytest.main(['-v', 'test_arczonalshift.py']))