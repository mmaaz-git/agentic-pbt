import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codestarconnections as csc

# This should fail because 'µ' is not ASCII alphanumeric
try:
    conn = csc.Connection(
        title='µ',
        ConnectionName='test'
    )
    print("ERROR: Should have raised ValueError")
except ValueError as e:
    print(f"Expected error: {e}")

# However, this is a Unicode letter character
print(f"'µ' is alpha: {'µ'.isalpha()}")
print(f"'µ' is alphanumeric: {'µ'.isalnum()}")