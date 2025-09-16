#!/usr/bin/env python3
"""Run property-based tests for pyramid_decorator."""

import sys
import subprocess

# Install dependencies
print("Installing dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "hypothesis", "pytest", "-q"])

# Run tests
print("\nRunning property-based tests...")
import pytest
sys.exit(pytest.main(["test_pyramid_decorator.py", "-v", "--tb=short"]))