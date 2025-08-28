import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.utils import glob_filter, shift_lineno
import types

# Bug 1: glob_filter directory pattern issue
print("=== Bug 1: glob_filter directory pattern ===")
pattern = "/tmp/testdir"
matcher = glob_filter(pattern)
test_file = "/tmp/testdir/file.txt"
result = matcher(test_file)
print(f"Pattern: {pattern}")
print(f"Test file: {test_file}")
print(f"Match result: {result}")
print(f"Expected: True (directory pattern should match files in directory)")

print("\n=== Let's debug what glob_filter does ===")
import os
import fnmatch

def debug_glob_filter(pattern):
    print(f"Input pattern: {pattern}")
    
    if pattern.startswith("~"):
        pattern = os.path.expanduser(pattern)
        print(f"After expanduser: {pattern}")
    elif not pattern.startswith("/"):
        pattern = os.path.abspath(pattern)
        print(f"After abspath: {pattern}")
    
    if os.path.isdir(pattern):
        pattern = os.path.join(pattern, "*")
        print(f"After isdir check (would add /*): {pattern}")
    else:
        print(f"Not a directory, pattern unchanged: {pattern}")
    
    def matcher(filename):
        result = fnmatch.fnmatch(filename, pattern)
        print(f"  fnmatch({filename}, {pattern}) = {result}")
        return result
    
    return matcher, pattern

matcher2, final_pattern = debug_glob_filter("/tmp/testdir")
print(f"Final pattern used: {final_pattern}")
print(f"Testing against: /tmp/testdir/file.txt")
result2 = matcher2("/tmp/testdir/file.txt")

print("\n=== Bug 2: shift_lineno with negative delta ===")
# Create a simple code object
code_str = """
def test():
    pass
"""
code_obj = compile(code_str, "test.py", "exec")
print(f"Original first line number: {code_obj.co_firstlineno}")

try:
    # This should fail
    shifted = shift_lineno(code_obj, -2)
    print(f"Shifted line number: {shifted.co_firstlineno}")
except ValueError as e:
    print(f"Error when shifting by -2: {e}")
    print("This is a bug - shift_lineno doesn't validate against negative line numbers")

# Test the round-trip property failure
print("\n=== Round-trip property violation ===")
print("If we shift by -2 then +2, we should get back the original")
print("But the function crashes when shifting would make line number < 1")