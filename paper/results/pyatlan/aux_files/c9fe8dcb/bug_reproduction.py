import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.model.utils import to_python_class_name
import keyword

# Bug 1: Returns Python keyword 'None'
print("Bug 1: Testing 'None' input")
result = to_python_class_name('None')
print(f"Input: 'None'")
print(f"Output: '{result}'")
print(f"Is keyword: {keyword.iskeyword(result)}")
print()

# Bug 2: Returns lowercase first character
print("Bug 2: Testing '0A' input")
result = to_python_class_name('0A')
print(f"Input: '0A'")
print(f"Output: '{result}'")
print(f"Starts with uppercase: {result[0].isupper() if result else 'Empty'}")
print()

# Additional test cases to understand the pattern
test_cases = ['True', 'False', '0Hello', '123World', '0']
for test in test_cases:
    result = to_python_class_name(test)
    print(f"Input: '{test}' -> Output: '{result}' (keyword: {keyword.iskeyword(result)})")