#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

import pytest

# Run just the failing tests
sys.exit(pytest.main(['test_dparse_updater_properties.py::test_requirements_txt_preserves_comments', '-v', '--tb=short', '--hypothesis-seed=0']))