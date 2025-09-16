#!/usr/bin/env python3
import sys
import os

# Add the optax env site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

# Now run pytest
import pytest

if __name__ == "__main__":
    # Run pytest with the test file
    sys.exit(pytest.main(['-v', 'test_optax_monte_carlo.py']))