import troposphere.route53recoverycontrol as r53rc

# Test 1: Empty string title
print("Test 1: Empty string title")
try:
    cluster = r53rc.Cluster(title="", Name="TestName")
    print(f"SUCCESS: Created cluster with empty title: {cluster.title}")
    print(f"Cluster name: {cluster.Name}")
    # Try to convert to dict to ensure it validates
    result = cluster.to_dict()
    print(f"to_dict() succeeded, Type: {result.get('Type')}")
except ValueError as e:
    print(f"FAILED: Empty title raised ValueError: {e}")

print("\n" + "="*50 + "\n")

# Test 2: None title
print("Test 2: None title")
try:
    cluster2 = r53rc.Cluster(title=None, Name="TestName")
    print(f"SUCCESS: Created cluster with None title: {cluster2.title}")
except ValueError as e:
    print(f"FAILED: None title raised ValueError: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Valid alphanumeric title
print("Test 3: Valid alphanumeric title")
try:
    cluster3 = r53rc.Cluster(title="ValidTitle123", Name="TestName") 
    print(f"SUCCESS: Created cluster with valid title: {cluster3.title}")
except ValueError as e:
    print(f"FAILED: Valid title raised ValueError: {e}")

print("\n" + "="*50 + "\n")

# Test 4: Invalid title with special characters
print("Test 4: Invalid title with special characters")
try:
    cluster4 = r53rc.Cluster(title="Invalid-Title", Name="TestName")
    print(f"SUCCESS: Created cluster with invalid title: {cluster4.title}")
except ValueError as e:
    print(f"FAILED: Invalid title raised ValueError: {e}")

print("\n" + "="*50 + "\n")

# Look at the validation code
print("Checking validation logic...")
import troposphere
import re

# This is the regex used for validation
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

# Test the regex
test_titles = ["", None, "ValidTitle", "Invalid-Title", "Title_With_Underscore", "123Numbers"]
for title in test_titles:
    if title:
        match = valid_names.match(title)
        print(f"Title '{title}': regex match = {match is not None}")
    else:
        print(f"Title '{title}': empty or None")

print("\n" + "="*50 + "\n")

# Check the actual validation method
print("Testing validate_title method directly...")
from troposphere import BaseAWSObject

class TestObject(BaseAWSObject):
    def __init__(self, title):
        self.title = title
        if self.title:
            self.validate_title()

# Test empty string
print("Empty string validation:")
try:
    obj1 = TestObject("")
    print("  Empty string was accepted (BUG!)")
except ValueError as e:
    print(f"  Empty string rejected: {e}")

# Test None
print("None validation:")
try:
    obj2 = TestObject(None)
    print("  None was accepted (expected - no validation if None)")
except ValueError as e:
    print(f"  None rejected: {e}")