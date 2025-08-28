import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

# Bug 1: ParseError not wrapped as InvalidEnvelopeExpressionError
print("=== BUG 1: ParseError not caught in query function ===")
from aws_lambda_powertools.utilities.jmespath_utils import query
from aws_lambda_powertools.exceptions import InvalidEnvelopeExpressionError
import jmespath.exceptions

data = {"test": "value"}
invalid_expression = "@@@@@"  # This causes ParseError, not LexerError

try:
    result = query(data, invalid_expression)
    print(f"ERROR: Should have raised an exception, got: {result}")
except InvalidEnvelopeExpressionError as e:
    print(f"EXPECTED: InvalidEnvelopeExpressionError raised")
except jmespath.exceptions.ParseError as e:
    print(f"BUG CONFIRMED: ParseError leaked through instead of being wrapped!")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error message: {e}")

# Bug 2: Special key with bracket causes unhandled ParseError
print("\n=== BUG 2: Bracket in dictionary key causes unhandled ParseError ===")

data_with_bracket_key = {"[": "value"}
key_to_query = "["

try:
    result = query(data_with_bracket_key, key_to_query)
    print(f"ERROR: Should have raised InvalidEnvelopeExpressionError, got: {result}")
except InvalidEnvelopeExpressionError as e:
    print(f"EXPECTED: InvalidEnvelopeExpressionError raised")
except jmespath.exceptions.ParseError as e:
    print(f"BUG CONFIRMED: ParseError leaked through!")
    print(f"  When querying key '[' in dictionary")
    print(f"  Error: {e}")

# Additional test - verify LexerError IS properly caught
print("\n=== Verification: LexerError is properly caught ===")
data = {"test": "value"}
expression_causing_lexer_error = "'"  # Unclosed quote causes LexerError

try:
    result = query(data, expression_causing_lexer_error)
    print(f"ERROR: Should have raised an exception, got: {result}")
except InvalidEnvelopeExpressionError as e:
    print(f"CORRECT: LexerError was properly wrapped as InvalidEnvelopeExpressionError")
except Exception as e:
    print(f"ERROR: Unexpected exception: {type(e).__name__}: {e}")