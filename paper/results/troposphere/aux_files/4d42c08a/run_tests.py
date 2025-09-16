#!/usr/bin/env python3
import sys
import os

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now run pytest
import pytest

# Run pytest on our test file
exit_code = pytest.main(['-v', '--tb=short', 'test_codegurureviewer.py'])
sys.exit(exit_code)