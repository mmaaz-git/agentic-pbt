#!/usr/bin/env python3
import subprocess
import sys

print("Installing troposphere...")
result = subprocess.run([sys.executable, "-m", "pip", "install", "troposphere"], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)

print("\nImporting troposphere.lakeformation...")
import troposphere.lakeformation
print(f"Module file: {troposphere.lakeformation.__file__}")