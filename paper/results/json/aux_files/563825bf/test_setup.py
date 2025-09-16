#!/usr/bin/env python3
import sys
print(f"Python version: {sys.version}")

try:
    import requests
    print("Requests is installed")
except ImportError:
    print("Requests is NOT installed")
    sys.exit(1)