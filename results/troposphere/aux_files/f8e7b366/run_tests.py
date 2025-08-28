#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import pytest

sys.exit(pytest.main(['-v', 'test_mwaa_properties.py']))