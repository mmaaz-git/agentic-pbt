import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.location as location

# Test case 1: Empty dict (should fail because required fields are missing)
print("Test 1: Empty dict (missing required fields KeyName and Restrictions)")
try:
    obj = location.APIKey.from_dict("TestKey", {})
    obj.validate()
    print("No error raised - this might be a bug")
except Exception as e:
    print(f"Raised {type(e).__name__}: {e}")

# Test case 2: Dict with invalid boolean value
print("\nTest 2: Dict with ForceDelete as empty string")
try:
    obj = location.APIKey.from_dict("TestKey", {"ForceDelete": ""})
    obj.validate()
    print("No error raised")
except ValueError as e:
    print(f"Raised ValueError: {e}")
except Exception as e:
    print(f"Raised {type(e).__name__}: {e}")

# Test case 3: Valid minimal dict
print("\nTest 3: Valid minimal dict with required fields")
try:
    valid_data = {
        "KeyName": "MyKey",
        "Restrictions": {
            "AllowActions": ["location:GetMap*"],
            "AllowResources": ["arn:aws:geo:*:*:map/*"]
        }
    }
    obj = location.APIKey.from_dict("TestKey", valid_data)
    obj.validate()
    print("Validation passed correctly")
except Exception as e:
    print(f"Raised {type(e).__name__}: {e}")