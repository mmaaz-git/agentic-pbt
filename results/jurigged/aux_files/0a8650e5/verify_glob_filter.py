import sys
import os
import tempfile
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.utils import glob_filter

# Test with an actual existing directory
with tempfile.TemporaryDirectory() as tmpdir:
    print(f"Created temp directory: {tmpdir}")
    
    # Create a test file in the directory
    test_file = os.path.join(tmpdir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("test")
    
    # Test glob_filter with existing directory
    matcher = glob_filter(tmpdir)
    result = matcher(test_file)
    print(f"Pattern (existing dir): {tmpdir}")
    print(f"Test file: {test_file}")
    print(f"Match result: {result}")
    print(f"Expected: True")
    
    # Also test with non-existing directory
    non_exist = "/tmp/definitely_does_not_exist_12345"
    matcher2 = glob_filter(non_exist)
    test_file2 = non_exist + "/file.txt"
    result2 = matcher2(test_file2)
    print(f"\nPattern (non-existing): {non_exist}")
    print(f"Test file: {test_file2}")
    print(f"Match result: {result2}")
    print(f"Expected: False (because directory doesn't exist)")