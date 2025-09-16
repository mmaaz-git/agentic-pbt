import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')
from isort import sorting

# Test natural sorting
test = ["file10", "file2", "file1"]
result = sorting.naturally(test)
print(f"Input: {test}")
print(f"Result: {result}")
print(f"Expected: ['file1', 'file2', 'file10']")
print(f"Match: {result == ['file1', 'file2', 'file10']}")