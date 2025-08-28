#!/usr/bin/env python3
"""Direct execution of tests to find bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

# Execute the focused hypothesis tests
exec(open('focused_hypothesis_test.py').read())