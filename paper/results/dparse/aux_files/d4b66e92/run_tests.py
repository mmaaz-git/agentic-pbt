#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

import pytest

# Run the tests
sys.exit(pytest.main(['test_dparse_updater_properties.py', '-v', '--tb=short']))