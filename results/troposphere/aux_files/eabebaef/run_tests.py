#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python
import subprocess
import sys

result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "test_troposphere_macie.py", 
    "-v", "--tb=short"
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)