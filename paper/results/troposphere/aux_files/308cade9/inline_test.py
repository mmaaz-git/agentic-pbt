import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Test backup_vault_name edge case
from troposphere.validators.backup import backup_vault_name

# The regex in the code is: r"^[a-zA-Z0-9\-\_\.]{1,50}$"
# Let's test some edge cases

print("Testing backup_vault_name:")

# Test 1: Empty string (should fail per regex)
try:
    result = backup_vault_name("")
    print(f"BUG FOUND: Empty string accepted as '{result}'")
except ValueError:
    print("OK: Empty string rejected")

# Test 2: Single special characters (should pass per regex)
for char in ["-", "_", "."]:
    try:
        result = backup_vault_name(char)
        print(f"OK: '{char}' accepted as '{result}'")
    except ValueError as e:
        print(f"BUG FOUND: '{char}' rejected with: {e}")

# Test 3: Check if boolean("1") really returns True (not "1")
from troposphere.validators import boolean

result = boolean("1")
print(f"\nboolean('1') returns: {result} (type: {type(result)})")
if result is True:
    print("OK: Returns True")
else:
    print(f"Potential issue: Returns {result}")

result = boolean(1)
print(f"boolean(1) returns: {result} (type: {type(result)})")

# Test 4: Check JSON checker behavior
from troposphere.validators import json_checker
import json

test_dict = {"key": "value"}
result1 = json_checker(test_dict)
print(f"\njson_checker(dict) returns: {repr(result1)}")

# Now pass the result back
result2 = json_checker(result1)
print(f"json_checker(json_str) returns: {repr(result2)}")

if result1 == result2:
    print("OK: json_checker is idempotent")
else:
    print("BUG: json_checker is not idempotent")

# Test 5: Check what happens with the regex directly
vault_name_re = re.compile(r"^[a-zA-Z0-9\-\_\.]{1,50}$")
test_strings = ["", "-", "_", ".", "a-b", "test.vault", "123"]

print("\nDirect regex tests:")
for s in test_strings:
    matches = bool(vault_name_re.match(s))
    print(f"  '{s}' matches: {matches}")