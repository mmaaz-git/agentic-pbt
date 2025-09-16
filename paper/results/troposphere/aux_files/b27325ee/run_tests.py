#!/usr/bin/env python3
import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now run pytest
import pytest

# Run the tests
sys.exit(pytest.main(['-v', 'test_backupgateway_properties.py']))