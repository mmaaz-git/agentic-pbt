import sys
import os

sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import files
from isort.settings import Config

config = Config()
skipped = []
broken = []

# Test with parent directory reference
print(f"Current directory: {os.getcwd()}")
print("Testing with '..'")

result_gen = files.find(['..'], config, skipped, broken)

# Take only first 10 results to see what's happening
results = []
for i, item in enumerate(result_gen):
    results.append(item)
    print(f"  Found: {item}")
    if i >= 9:
        break

print(f"\nTotal shown: {len(results)} (limited to 10)")
print(f"Skipped: {skipped}")
print(f"Broken: {broken}")