import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.mediaconvert as mc

# Test required field validation
try:
    jt = mc.JobTemplate("Test")
    result = jt.to_dict()
    print(f"ERROR: Should have failed without SettingsJson")
except ValueError as e:
    print(f"Expected error: {e}")

# Test with required field
jt2 = mc.JobTemplate("Test2", SettingsJson={"key": "value"})
print(f"Valid object created: {jt2.to_dict()}")

# Test property type validation with Priority
jt3 = mc.JobTemplate("Test3", SettingsJson={})
jt3.Priority = 5
print(f"Integer Priority accepted: {jt3.Priority}")

try:
    jt3.Priority = "not_an_integer"
    print(f"ERROR: String Priority should fail validation")
except ValueError as e:
    print(f"Expected validation error for Priority: {e}")