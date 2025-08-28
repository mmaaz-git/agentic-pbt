#!/usr/bin/env python3
import sys
import os

# Add the isal environment to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

# Now run pytest
import pytest

# Run the tests
sys.exit(pytest.main(['-v', 'test_igzip_threaded_edge_cases.py']))