import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import organizations

# Minimal reproduction of the empty title bug
def test_empty_title_bug():
    # According to the validate_title method in BaseAWSObject,
    # titles must match r'^[a-zA-Z0-9]+$' which requires at least one character
    # Empty string does not match this pattern
    
    # Test 1: Empty string should be rejected
    print("Test 1: Creating Organization with empty title...")
    try:
        org = organizations.Organization(title="")
        dict_repr = org.to_dict()
        print(f"  Result: Accepted empty title! dict_repr={dict_repr}")
        print(f"  org.title = {repr(org.title)}")
        return True  # Bug found
    except ValueError as e:
        print(f"  Result: Correctly rejected: {e}")
        return False
    
# Run the test
if __name__ == "__main__":
    bug_found = test_empty_title_bug()
    if bug_found:
        print("\nBUG CONFIRMED: Empty string is incorrectly accepted as a valid title")
        print("Expected: ValueError should be raised for empty title")
        print("Actual: Empty title is accepted")
    else:
        print("\nNo bug - empty title is correctly rejected")