import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import json
import base64
from aws_lambda_powertools.utilities.serialization import base64_from_json
from aws_lambda_powertools.utilities.jmespath_utils import query
from aws_lambda_powertools.exceptions import InvalidEnvelopeExpressionError
import jmespath

# 1. Test NaN/Infinity handling in base64_from_json
print("=== Testing NaN/Infinity in base64_from_json ===")
try:
    result = base64_from_json(float('nan'))
    print(f"NaN encoded successfully: {result}")
    decoded = json.loads(base64.b64decode(result).decode())
    print(f"Decoded value: {decoded}, type: {type(decoded)}")
except Exception as e:
    print(f"NaN encoding failed with: {type(e).__name__}: {e}")

try:
    result = base64_from_json(float('inf'))
    print(f"Infinity encoded successfully: {result}")
    decoded = json.loads(base64.b64decode(result).decode())
    print(f"Decoded value: {decoded}, type: {type(decoded)}")
except Exception as e:
    print(f"Infinity encoding failed with: {type(e).__name__}: {e}")

# 2. Test JMESPath with special characters in keys
print("\n=== Testing JMESPath with special key names ===")
test_cases = [
    {"'": "value1"},  # Single quote in key
    {"@": "value2"},  # @ symbol
    {"[": "value3"},  # Bracket
    {"*": "value4"},  # Asterisk
]

for data in test_cases:
    key = list(data.keys())[0]
    print(f"\nTesting key: {repr(key)}")
    try:
        result = query(data, key)
        print(f"  Query succeeded: {result}")
    except InvalidEnvelopeExpressionError as e:
        print(f"  InvalidEnvelopeExpressionError: {e}")
    except jmespath.exceptions.LexerError as e:
        print(f"  JMESPath LexerError (not wrapped!): {e}")
    except jmespath.exceptions.ParseError as e:
        print(f"  JMESPath ParseError (not wrapped!): {e}")
    except Exception as e:
        print(f"  Unexpected error {type(e).__name__}: {e}")

# 3. Test what exceptions are caught and wrapped
print("\n=== Testing exception wrapping in query function ===")
invalid_expressions = [
    "@@@@@",  # Multiple @ symbols
    "[][]",   # Invalid bracket sequence
    "''",     # Empty quotes
    "**",     # Multiple asterisks
]

for expr in invalid_expressions:
    print(f"\nTesting expression: {repr(expr)}")
    try:
        result = query({"test": "value"}, expr)
        print(f"  Unexpectedly succeeded: {result}")
    except InvalidEnvelopeExpressionError as e:
        print(f"  Correctly wrapped as InvalidEnvelopeExpressionError")
    except jmespath.exceptions.ParseError as e:
        print(f"  NOT WRAPPED: ParseError leaked through!")
    except jmespath.exceptions.LexerError as e:
        print(f"  NOT WRAPPED: LexerError leaked through!")  
    except Exception as e:
        print(f"  Other exception {type(e).__name__}: {e}")