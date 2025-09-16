#!/usr/bin/env python3
"""Manual property tests for copier._user_data."""

import sys
import json
import yaml

# Add the copier environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._user_data import (
    AnswersMap,
    Question,
    parse_yaml_string,
    parse_yaml_list,
    CAST_STR_TO_NATIVE,
)
from jinja2.sandbox import SandboxedEnvironment

print("Testing copier._user_data module...")
print("=" * 60)

# Test 1: parse_yaml_string round-trip
print("\n1. Testing parse_yaml_string round-trip...")
test_values = [
    None,
    True,
    False,
    42,
    3.14,
    "hello",
    [1, 2, 3],
    {"key": "value"},
]

for value in test_values:
    yaml_str = yaml.safe_dump(value)
    parsed = parse_yaml_string(yaml_str)
    if isinstance(value, float):
        assert abs(parsed - value) < 1e-9, f"Failed for {value}"
    else:
        assert parsed == value, f"Failed for {value}: got {parsed}"
print("✓ parse_yaml_string round-trip works correctly")

# Test 2: parse_yaml_list behavior
print("\n2. Testing parse_yaml_list...")
# Valid list
yaml_list_str = "- item1\n- item2\n- 123"
result = parse_yaml_list(yaml_list_str)
assert isinstance(result, list), "Should return a list"
assert len(result) == 3, f"Expected 3 items, got {len(result)}"
print(f"  Parsed list: {result}")

# Invalid input (not a list)
try:
    parse_yaml_list("not a list")
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("✓ parse_yaml_list works correctly")

# Test 3: AnswersMap.combined priority
print("\n3. Testing AnswersMap.combined priority...")
answers = AnswersMap(
    user={"a": 1, "b": 2},
    init={"b": 20, "c": 30},
    metadata={"c": 300, "d": 400},
    last={"d": 4000, "e": 5000},
    user_defaults={"e": 50000, "f": 60000}
)
combined = answers.combined

# Check priority: user > init > metadata > last > user_defaults
assert combined["a"] == 1, "user value should win"
assert combined["b"] == 2, "user should override init"
assert combined["c"] == 30, "init should override metadata"
assert combined["d"] == 400, "metadata should override last"
assert combined["e"] == 5000, "last should override user_defaults"
assert combined["f"] == 60000, "user_defaults value should be present"
print("✓ AnswersMap.combined priority works correctly")

# Test 4: Type casting functions
print("\n4. Testing type casting functions...")
# Test bool casting
bool_cast = CAST_STR_TO_NATIVE["bool"]
assert bool_cast("true") == True
assert bool_cast("false") == False
assert bool_cast("yes") == True
assert bool_cast("no") == False
assert bool_cast("1") == True
assert bool_cast("0") == False

# Test int casting
int_cast = CAST_STR_TO_NATIVE["int"]
assert int_cast("42") == 42
assert int_cast("-5") == -5
assert int_cast("0") == 0

# Test float casting
float_cast = CAST_STR_TO_NATIVE["float"]
assert float_cast("3.14") == 3.14
assert float_cast("-2.5") == -2.5
assert float_cast("1e10") == 1e10

print("✓ Type casting functions work correctly")

# Test 5: Question type casting
print("\n5. Testing Question type casting...")
question = Question(
    var_name="test_var",
    answers=AnswersMap(),
    context={},
    jinja_env=SandboxedEnvironment(),
    type="int"
)

# Test casting string to int
casted = question.cast_answer("42")
assert casted == 42
assert isinstance(casted, int)

# Test with bool type
bool_question = Question(
    var_name="test_bool",
    answers=AnswersMap(),
    context={},
    jinja_env=SandboxedEnvironment(),
    type="bool"
)
bool_casted = bool_question.cast_answer("true")
assert bool_casted == True
assert isinstance(bool_casted, bool)

print("✓ Question type casting works correctly")

# Test 6: Edge case - parse_yaml_list with quoted strings
print("\n6. Testing parse_yaml_list with special cases...")
yaml_with_quotes = '''
- "quoted string"
- 'single quoted'
- unquoted
- 123
- true
'''
parsed_list = parse_yaml_list(yaml_with_quotes.strip())
print(f"  Parsed items: {parsed_list}")
assert len(parsed_list) == 5

# Check that quotes are stripped properly
assert parsed_list[0] == "quoted string", f"Expected 'quoted string', got {parsed_list[0]}"
assert parsed_list[1] == "single quoted", f"Expected 'single quoted', got {parsed_list[1]}"

print("✓ parse_yaml_list handles quoted strings correctly")

print("\n" + "=" * 60)
print("All manual tests passed ✓")