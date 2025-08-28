#!/usr/bin/env python3
"""Run the troposphere amplify tests with correct path."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now import and run the tests
import pytest

if __name__ == "__main__":
    pytest.main(['test_troposphere_amplify.py', '-v', '--tb=short'])