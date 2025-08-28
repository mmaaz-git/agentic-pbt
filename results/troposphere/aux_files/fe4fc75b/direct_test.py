import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Test 1: Boolean validator with "1" vs 1
from troposphere import validators

print("TEST 1: Boolean validator inconsistency")
print(f"boolean('1') = {validators.boolean('1')}")  
print(f"boolean(1) = {validators.boolean(1)}")
print(f"boolean('0') = {validators.boolean('0')}")
print(f"boolean(0) = {validators.boolean(0)}")

# But what about edge cases?
test_cases = ["TRUE", "FALSE", "Yes", "No", 1.0, 0.0, "t", "f", " true", "true "]
for tc in test_cases:
    try:
        result = validators.boolean(tc)
        print(f"boolean({repr(tc)}) = {result}")
    except ValueError:
        print(f"boolean({repr(tc)}) raises ValueError")

print("\nTEST 2: Check Pipeline validation")
from troposphere import datapipeline

# Create pipeline with valid title
p = datapipeline.Pipeline("ValidTitle123")

# Try to get dict without setting required Name field
try:
    d = p.to_dict()
    print(f"Pipeline.to_dict() without Name: {d}")
except ValueError as e:
    print(f"Pipeline.to_dict() without Name raises: {e}")

# Now set Name and try again
p.Name = "TestPipeline"
d = p.to_dict()
print(f"Pipeline.to_dict() with Name: {d}")

print("\nTEST 3: Empty string handling")
# What happens with empty strings?
try:
    p2 = datapipeline.Pipeline("")
    print("Empty title accepted - potential bug!")
except ValueError as e:
    print(f"Empty title rejected: {e}")

print("\nTEST 4: Special handling of boolean Activate field")
p3 = datapipeline.Pipeline("TestPipe")
p3.Name = "Test"

# Test the Activate field with edge cases
p3.Activate = "true"
print(f"After setting Activate='true': {p3.Activate}")

p3.Activate = 1  
print(f"After setting Activate=1: {p3.Activate}")

p3.Activate = "1"
print(f"After setting Activate='1': {p3.Activate}")

print("\nTEST 5: ObjectField with edge cases")
# Can we set only Key?
field1 = datapipeline.ObjectField(Key="test")
print(f"ObjectField with only Key: {field1.to_dict()}")

# What about empty Key?
try:
    field2 = datapipeline.ObjectField(Key="")
    print(f"ObjectField with empty Key: {field2.to_dict()}")
except Exception as e:
    print(f"ObjectField with empty Key raises: {e}")

print("\nTEST 6: List validation")
# Can we pass non-list to list properties?
try:
    param = datapipeline.ParameterObject(
        Id="test",
        Attributes="not a list"  # Should be a list
    )
    print(f"ParameterObject with string Attributes: {param.to_dict()}")
except TypeError as e:
    print(f"ParameterObject with string Attributes raises: {e}")