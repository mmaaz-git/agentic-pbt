from packaging.requirements import Requirement

print("Testing round-trip property with URLs containing whitespace:")

test_cases = [
    'package @ https://example.com ',
    'package @  https://example.com',  # multiple spaces
    'package @ https://example.com/path ',
    'pkg @ file:///some/path ',
]

for req_str in test_cases:
    print(f"\nOriginal: {repr(req_str)}")
    
    req1 = Requirement(req_str)
    print(f"  URL after first parse: {repr(req1.url)}")
    
    # Convert back to string
    str_repr = str(req1)
    print(f"  String representation: {repr(str_repr)}")
    
    # Parse again
    req2 = Requirement(str_repr)
    print(f"  URL after round-trip: {repr(req2.url)}")
    
    # Check if semantically equivalent
    print(f"  URLs match: {req1.url == req2.url}")
    
print("\n" + "="*60)
print("Testing if whitespace stripping could cause actual issues:")

# Case 1: URLs that might legitimately have spaces (though rare)
url_with_space = "https://example.com/path%20with%20spaces "
req_str = f"package @ {url_with_space}"
req = Requirement(req_str)
print(f"\nURL with encoded spaces:")
print(f"  Input:  {repr(url_with_space)}")
print(f"  Output: {repr(req.url)}")
print(f"  Match:  {req.url == url_with_space}")

# Case 2: File URLs with spaces in paths
file_url = "file:///path/to/my file "
req_str2 = f"package @ {file_url}"
try:
    req2 = Requirement(req_str2)
    print(f"\nFile URL with space in path:")
    print(f"  Input:  {repr(file_url)}")
    print(f"  Output: {repr(req2.url)}")
    print(f"  Match:  {req2.url == file_url}")
except Exception as e:
    print(f"\nFile URL with space: ERROR - {e}")