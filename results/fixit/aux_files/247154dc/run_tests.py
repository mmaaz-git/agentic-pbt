#!/usr/bin/env python3
"""
Runner script to execute tests with proper module paths.
"""

import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

# Now run the tests
if __name__ == "__main__":
    # Import and run the test module
    import test_fixit_properties
    import pytest
    
    # Run pytest on the test module
    exit_code = pytest.main(['test_fixit_properties.py', '-v', '--tb=short'])
    sys.exit(exit_code)