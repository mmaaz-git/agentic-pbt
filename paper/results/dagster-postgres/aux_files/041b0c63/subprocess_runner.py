#!/usr/bin/env python3
import subprocess
import sys

# First test imports
print("Running import test...")
result = subprocess.run(
    ['/root/hypothesis-llm/envs/dagster-postgres_env/bin/python', 'test_import.py'],
    capture_output=True,
    text=True,
    cwd='/root/hypothesis-llm/worker_/11'
)

print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}")
print("-" * 60)

# Run minimal hypothesis test
print("\nRunning hypothesis property test...")
result2 = subprocess.run(
    ['/root/hypothesis-llm/envs/dagster-postgres_env/bin/python', 'minimal_hypothesis_test.py'],
    capture_output=True,
    text=True,
    cwd='/root/hypothesis-llm/worker_/11'
)

print("STDOUT:")
print(result2.stdout)
if result2.stderr:
    print("STDERR:")
    print(result2.stderr)
print(f"Return code: {result2.returncode}")