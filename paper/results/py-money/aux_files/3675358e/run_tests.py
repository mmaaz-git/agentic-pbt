#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", "test_currency_properties.py"]))