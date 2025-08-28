#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.auditmanager
import inspect

print("Module imported successfully")
print(f"Module file: {troposphere.auditmanager.__file__}")