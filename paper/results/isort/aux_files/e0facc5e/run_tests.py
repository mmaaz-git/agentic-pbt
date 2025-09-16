#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import pytest

# Run pytest with our test file
sys.exit(pytest.main(['test_isort_parse.py', '-v', '--tb=short']))