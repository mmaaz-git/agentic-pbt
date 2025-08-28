#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import subprocess
import sys

result = subprocess.run([sys.executable, "-m", "pytest", "test_limits_storage.py", "-v", "--tb=short"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)