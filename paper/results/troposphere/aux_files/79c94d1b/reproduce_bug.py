"""Minimal reproduction of the title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.comprehend import DocumentClassifier, DocumentClassifierInputDataConfig

# Test 1: Empty string should fail validation but doesn't
print("Test 1: Empty string as title")
try:
    obj = DocumentClassifier("", 
                            DataAccessRoleArn="arn",
                            DocumentClassifierName="test",
                            InputDataConfig=DocumentClassifierInputDataConfig(),
                            LanguageCode="en")
    print(f"SUCCESS: Created object with empty title: {obj.title!r}")
    print("BUG: Empty string should not be allowed as alphanumeric!")
except ValueError as e:
    print(f"Failed as expected: {e}")

print("\n" + "="*50 + "\n")

# Test 2: Newline character causes regex matching issues  
print("Test 2: Newline character as title")
try:
    obj = DocumentClassifier("\n",
                            DataAccessRoleArn="arn", 
                            DocumentClassifierName="test",
                            InputDataConfig=DocumentClassifierInputDataConfig(),
                            LanguageCode="en")
    print(f"SUCCESS: Created object with newline title: {obj.title!r}")
    print("BUG: Newline should not be allowed as alphanumeric!")
except ValueError as e:
    print(f"Failed as expected with error: {e!r}")
    # The error message contains the newline which can break regex patterns
    print(f"Error message repr: {str(e)!r}")