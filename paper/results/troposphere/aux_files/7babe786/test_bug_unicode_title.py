"""Test for Unicode title bug in from_dict"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codepipeline as cp

# Test 1: Direct construction with Unicode title fails
print("Test 1: Direct construction with Unicode title")
try:
    artifact = cp.ArtifactDetails(
        title='µ',
        MaximumCount=1,
        MinimumCount=0
    )
    print("  SUCCESS: Created with Unicode title")
except ValueError as e:
    print(f"  FAILED: {e}")

# Test 2: from_dict with Unicode title also fails 
print("\nTest 2: from_dict with Unicode title")
try:
    artifact = cp.ArtifactDetails.from_dict('µ', {
        'MaximumCount': 1,
        'MinimumCount': 0
    })
    print("  SUCCESS: Created from dict with Unicode title")
except ValueError as e:
    print(f"  FAILED: {e}")
    
# Test 3: What if we bypass validation?
print("\nTest 3: Bypassing validation")
try:
    artifact = cp.ArtifactDetails(
        title='µ',
        MaximumCount=1,
        MinimumCount=0,
        validation=False
    )
    print(f"  SUCCESS: Created with validation=False, title='{artifact.title}'")
    
    # Can we convert to dict?
    dict_repr = artifact.to_dict(validation=False)
    print(f"  SUCCESS: Converted to dict: {dict_repr}")
    
    # Can we reconstruct from dict?
    reconstructed = cp.ArtifactDetails.from_dict('µ', dict_repr)
    print(f"  SUCCESS: Reconstructed from dict")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 4: Test that the error message is misleading
print("\nTest 4: Error message accuracy")
unicode_char = 'µ'
print(f"  Character '{unicode_char}':")
print(f"    - Python's isalnum(): {unicode_char.isalnum()}")
print(f"    - Python's isalpha(): {unicode_char.isalpha()}")
print(f"    - Unicode category: {__import__('unicodedata').category(unicode_char)}")
print(f"    - troposphere error: 'not alphanumeric' (but it IS alphanumeric!)")