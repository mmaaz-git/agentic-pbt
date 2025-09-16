#!/usr/bin/env python3
"""
Direct bug testing for multi_key_dict - Execute to find bugs
"""
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')
os.chdir('/root/hypothesis-llm/worker_/1')

# Import and run the minimal bug reproducer
print("=" * 70)
print("RUNNING BUG TESTS FOR multi_key_dict")
print("=" * 70)

exec(open('minimal_bug_reproducer.py').read())

# Also run the hypothesis tests
print("\n\n" + "=" * 70)
print("RUNNING HYPOTHESIS-BASED TESTS")
print("=" * 70)

exec(open('hypothesis_bug_finder.py').read())