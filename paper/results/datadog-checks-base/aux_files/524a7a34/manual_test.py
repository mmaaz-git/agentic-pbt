import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

# Import InquirerPy components
print("Testing InquirerPy properties manually...")

# Test 1: Test Separator string representation
from InquirerPy.separator import Separator

print("\n1. Testing Separator string representation:")
test_strings = ["---", "===", "Custom Line", "", "   ", "•••"]
for s in test_strings:
    sep = Separator(s)
    result = str(sep)
    if result == s:
        print(f"  ✓ Separator('{s}') -> '{result}' (correct)")
    else:
        print(f"  ✗ BUG: Separator('{s}') -> '{result}' (expected '{s}')")

# Test 2: Test _get_questions conversion
from InquirerPy.resolver import _get_questions
from InquirerPy.exceptions import InvalidArgument

print("\n2. Testing _get_questions dict/list conversion:")

# Test dict to list conversion
test_dict = {"type": "input", "message": "Test"}
result = _get_questions(test_dict)
if isinstance(result, list) and len(result) == 1 and result[0] == test_dict:
    print(f"  ✓ Dict correctly converted to list")
else:
    print(f"  ✗ BUG: Dict conversion failed: {result}")

# Test list passthrough
test_list = [{"type": "input"}, {"type": "confirm"}]
result = _get_questions(test_list)
if result == test_list and result is test_list:
    print(f"  ✓ List correctly passed through")
else:
    print(f"  ✗ BUG: List not passed through correctly")

# Test invalid input
try:
    _get_questions("invalid")
    print(f"  ✗ BUG: String input incorrectly accepted")
except InvalidArgument:
    print(f"  ✓ String input correctly rejected")

# Test 3: Test EmptyInputValidator
from InquirerPy.validator import EmptyInputValidator
from prompt_toolkit.validation import ValidationError

class FakeDocument:
    def __init__(self, text):
        self.text = text
        self.cursor_position = len(text)

print("\n3. Testing EmptyInputValidator:")
validator = EmptyInputValidator()

# Test empty strings (should fail validation)
empty_tests = ["", ]
for test in empty_tests:
    doc = FakeDocument(test)
    try:
        validator.validate(doc)
        print(f"  ✗ BUG: Empty string '{test}' incorrectly accepted")
    except ValidationError:
        print(f"  ✓ Empty string correctly rejected")

# Test non-empty strings (should pass validation)
non_empty_tests = [" ", "a", "test", "\n", "\t"]
for test in non_empty_tests:
    doc = FakeDocument(test)
    try:
        validator.validate(doc)
        print(f"  ✓ Non-empty string '{repr(test)}' correctly accepted")
    except ValidationError:
        print(f"  ✗ BUG: Non-empty string '{repr(test)}' incorrectly rejected")

print("\nManual testing complete.")