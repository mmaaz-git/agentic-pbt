import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.validators as validators
import troposphere.osis as osis

print("=== Bug 1: Boolean validator accepts float 0.0 ===")
try:
    result = validators.boolean(0.0)
    print(f"validators.boolean(0.0) returned: {result}")
    print(f"Type: {type(result)}")
    print("BUG: Should have raised ValueError for float input")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\n=== Bug 2: Boolean validator accepts float 1.0 ===")
try:
    result = validators.boolean(1.0)
    print(f"validators.boolean(1.0) returned: {result}")
    print(f"Type: {type(result)}")
    print("BUG: Should have raised ValueError for float input")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\n=== Bug 3: Integer validator accepts float 0.5 ===")
try:
    result = validators.integer(0.5)
    print(f"validators.integer(0.5) returned: {result}")
    print(f"int(result) = {int(result)}")
    print("BUG: Should have raised ValueError for non-integer float")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\n=== Bug 4: Integer validator accepts float 10.0 ===")
try:
    result = validators.integer(10.0)
    print(f"validators.integer(10.0) returned: {result}")
    print(f"int(result) = {int(result)}")
    print("NOTE: Accepting integer-valued floats might be intentional")
except ValueError as e:
    print(f"Raised ValueError: {e}")

print("\n=== Bug 5: VpcOptions doesn't handle None for optional properties ===")
try:
    vpc_opts = osis.VpcOptions(
        SubnetIds=['subnet-1'],
        SecurityGroupIds=None  # This is an optional property
    )
    print(f"Created VpcOptions with SecurityGroupIds=None: {vpc_opts}")
    print("BUG: Should accept None for optional properties")
except TypeError as e:
    print(f"Raised TypeError: {e}")
    print("This prevents setting optional properties to None explicitly")

print("\n=== Bug 6: Title validation inconsistency with Unicode alphanumeric ===")
# The character '¹' is considered alphanumeric by Python but not by the regex
test_char = '¹'
print(f"Character: {test_char}")
print(f"Python isalnum(): {test_char.isalnum()}")
print(f"Python isascii(): {test_char.isascii()}")

try:
    pipeline = osis.Pipeline(
        test_char,
        MinUnits=1,
        MaxUnits=2,
        PipelineName="test",
        PipelineConfigurationBody="test"
    )
    print("Pipeline created successfully")
except ValueError as e:
    print(f"Pipeline creation failed: {e}")
    print("BUG: Inconsistency between Python's isalnum() and the regex validation")