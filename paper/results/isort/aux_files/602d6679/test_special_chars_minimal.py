import sys
import os
import tempfile

sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import files
from isort.settings import Config

config = Config()
skipped = []
broken = []

# Test specific special characters that might cause issues
test_cases = [
    ['*'],
    ['?'],
    ['..'],
    ['./'],
    ['\\'],
    [':'],
    ['<>'],
    ['|'],
]

with tempfile.TemporaryDirectory() as tmpdir:
    for i, special_paths in enumerate(test_cases):
        print(f"Testing case {i}: {special_paths}")
        full_paths = [os.path.join(tmpdir, p) for p in special_paths]
        
        try:
            # Use timeout via iterator limit
            result_gen = files.find(full_paths, config, [], [])
            results = []
            for j, item in enumerate(result_gen):
                results.append(item)
                if j > 100:  # Prevent infinite iteration
                    print(f"  WARNING: Too many results, stopping")
                    break
            print(f"  OK: {len(results)} results")
        except Exception as e:
            print(f"  ERROR: {e}")