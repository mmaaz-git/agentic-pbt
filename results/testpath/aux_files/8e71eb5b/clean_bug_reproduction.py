#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

from testpath.tempdir import NamedFileInTemporaryDirectory

# Attempting to open a non-existent file in read mode
try:
    with NamedFileInTemporaryDirectory('test.txt', mode='r') as f:
        pass
except FileNotFoundError:
    print("FileNotFoundError caught (expected)")

print("Script completed, but check for AttributeError warnings above")