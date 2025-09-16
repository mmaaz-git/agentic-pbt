import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.format as fmt

# Bug 2: remove_whitespace doesn't remove tabs
content = "\ttest\t"
print(f"Input: {repr(content)}")

result = fmt.remove_whitespace(content)
print(f"Output: {repr(result)}")
print(f"Expected: {repr('test')}")

print(f"\nBug: Tabs are not removed by remove_whitespace()")
print(f"The function only removes spaces and newlines, not tabs")