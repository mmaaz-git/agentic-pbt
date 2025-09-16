#!/usr/bin/env python3
"""Run property-based tests for troposphere.backup module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import and run the tests
import test_troposphere_backup
import pytest

# Run the tests
result = pytest.main([
    'test_troposphere_backup.py', 
    '-v',
    '--tb=short',
    '--hypothesis-show-statistics'
])

sys.exit(result)