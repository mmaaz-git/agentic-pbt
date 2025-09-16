"""Minimal reproduction of potential bug in fire.testutils.assertOutputMatches"""

import sys
import fire.testutils

# Create a test case instance
test_case = fire.testutils.BaseTestCase()
test_case.setUp()

# Test case 1: stdout has output when None expected, stderr has no output when None expected
print("\nTest 1: stdout='0', stderr='', stdout_pattern=None, stderr_pattern='0'")
try:
    with test_case.assertOutputMatches(stdout=None, stderr='0'):
        sys.stdout.write('0')
        sys.stderr.write('')
except AssertionError as e:
    print(f"Error: {e}")
    # The error only mentions stdout, not that stderr doesn't match '0'
    # Expected: Should also mention that stderr '' doesn't match '0'
    
print("\n" + "="*50)

# Test case 2: Better example - both should fail
print("\nTest 2: Both stdout and stderr should fail")
print("stdout='hello', stderr='world', stdout_pattern=None, stderr_pattern=None")
try:
    with test_case.assertOutputMatches(stdout=None, stderr=None):
        sys.stdout.write('hello')
        sys.stderr.write('world')
except AssertionError as e:
    print(f"Error: {e}")
    # Only reports the first error (stdout), not both

print("\n" + "="*50)

# Test case 3: What about when both fail with patterns?
print("\nTest 3: Both fail with patterns")
print("stdout='hello', stderr='world', stdout_pattern='goodbye', stderr_pattern='universe'")
try:
    with test_case.assertOutputMatches(stdout='goodbye', stderr='universe'):
        sys.stdout.write('hello')
        sys.stderr.write('world')
except AssertionError as e:
    print(f"Error: {e}")
    # Again, only reports the first error

print("\n" + "="*50)
print("\nConclusion: assertOutputMatches only reports the first assertion failure,")
print("not all failures. This might be intentional design or a limitation.")