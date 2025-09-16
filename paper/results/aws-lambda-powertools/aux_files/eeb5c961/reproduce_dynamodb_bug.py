import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer

# Minimal reproduction of the DynamoDB deserializer bug
deserializer = TypeDeserializer()

# This number has 40 digits
number_str = '1000000000000000000000000000000000000010'
dynamodb_value = {"N": number_str}

print(f"Attempting to deserialize: {number_str}")
print(f"Length: {len(number_str)} digits")

try:
    result = deserializer.deserialize(dynamodb_value)
    print(f"Success: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    print("\nThis is a bug - the deserializer should handle numbers over 38 digits gracefully")