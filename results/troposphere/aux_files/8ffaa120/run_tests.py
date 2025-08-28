#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Run pytest programmatically
import pytest

# Run the tests
sys.exit(pytest.main(['-v', 'test_troposphere_iotsitewise.py']))