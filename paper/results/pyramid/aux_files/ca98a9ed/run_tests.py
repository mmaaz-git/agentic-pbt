#!/usr/bin/env python
"""Runner script to execute the property-based tests"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pytest
import os

# Change to the script directory
os.chdir('/root/hypothesis-llm/worker_/9')

# Run pytest
sys.exit(pytest.main(['-xvs', 'test_pyramid_events.py']))