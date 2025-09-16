#!/usr/bin/env python3
"""
Simple test runner for property-based tests
"""
import sys
import os

# Add the limits package to path
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

# Change to the test directory
os.chdir('/root/hypothesis-llm/worker_/14')

# Import and run the tests
exec(open('test_limits_strategies.py').read())