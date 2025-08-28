#!/usr/bin/env python3

import sys
import os

# Add the troposphere directory to the path
sys.path.insert(0, '/root/hypothesis-llm/worker_/1/troposphere-4.9.3')

# Try to import and monkeypatch if needed
try:
    from troposphere.ivschat import Room
    print("Successfully imported Room")
except ImportError as e:
    print(f"Import failed: {e}")
    # Try to mock cfn_flip
    import types
    sys.modules['cfn_flip'] = types.ModuleType('cfn_flip')
    # Now try again
    from troposphere.ivschat import Room
    print("Successfully imported Room after mocking cfn_flip")