#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

try:
    import tokenizers.tools
    print("Module imported successfully!")
    print(f"Module file: {tokenizers.tools.__file__}")
except ImportError as e:
    print(f"Failed to import: {e}")