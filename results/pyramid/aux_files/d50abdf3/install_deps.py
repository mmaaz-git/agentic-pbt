#!/usr/bin/env python3
import subprocess
import sys

# Install pyramid and test dependencies
subprocess.check_call([sys.executable, "-m", "pip", "install", "pyramid", "hypothesis", "pytest"])
print("Dependencies installed successfully")