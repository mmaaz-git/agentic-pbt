#!/usr/bin/env python3
import sys
import os

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import pytest

# Run the tests
sys.exit(pytest.main(['-v', 'test_package_logger_properties.py']))