#!/usr/bin/env python3
"""Runner script to execute tests with the correct Python environment."""

import sys
import subprocess

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

# Now import and run the tests
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(['test_trino_mapper_properties.py', '-v', '--tb=short']))