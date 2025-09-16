#!/usr/bin/env python3
"""Run the property-based tests for copier._types."""

import sys
import os

# Add copier env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

# Now import and run pytest
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(['-v', 'test_copier_types.py']))