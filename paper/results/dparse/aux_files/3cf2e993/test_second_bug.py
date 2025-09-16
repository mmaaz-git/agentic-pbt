#!/usr/bin/env python3
"""Test for second bug: typo in option name"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

print("Checking SetupCfgParser option names...")
print("=" * 60)

# Check what the standard setuptools options actually are
print("\nStandard setuptools options in setup.cfg [options] section:")
print("  - install_requires")
print("  - setup_requires") 
print("  - tests_require (note the 's')")
print("  - python_requires")
print("  - extras_require")
print()

# Look at the code
print("What dparse is looking for (line 417):")
print("  options = 'install_requires', 'setup_requires', 'test_require'")
print("                                                    ^^^^^^^^^^^^")
print("  Missing 's' - should be 'tests_require'")
print()

print("This is a second bug: The parser will never find 'tests_require'")
print("dependencies because it's looking for the wrong option name.")
print()

# This would be the corrected line 417:
print("Correct version should be:")
print("  options = 'install_requires', 'setup_requires', 'tests_require'")
print("                                                    ^^^^^")
print("=" * 60)