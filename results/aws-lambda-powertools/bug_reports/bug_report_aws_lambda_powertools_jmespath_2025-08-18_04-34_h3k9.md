# Bug Report: aws_lambda_powertools.utilities.jmespath_utils ParseError Not Wrapped

**Target**: `aws_lambda_powertools.utilities.jmespath_utils.query`
**Severity**: Medium  
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `query` function fails to wrap `jmespath.exceptions.ParseError` as `InvalidEnvelopeExpressionError`, violating its documented exception contract.

## Property-Based Test

```python
@given(st.text(alphabet='!@#$%^&*()[]{}|\\', min_size=5, max_size=20))
def test_query_invalid_expression(invalid_expr):
    """Test that invalid JMESPath expressions raise appropriate errors"""
    data = {"test": "value"}
    
    try:
        result = query(data, invalid_expr)
    except InvalidEnvelopeExpressionError:
        pass  # Expected
    except Exception as e:
        pytest.fail(f"Unexpected exception type: {type(e)}")
```

**Failing input**: `'@@@@@'`

## Reproducing the Bug

```python
from aws_lambda_powertools.utilities.jmespath_utils import query
from aws_lambda_powertools.exceptions import InvalidEnvelopeExpressionError
import jmespath.exceptions

data = {"test": "value"}
invalid_expression = "@@@@@"

try:
    result = query(data, invalid_expression)
except InvalidEnvelopeExpressionError:
    print("Expected behavior")
except jmespath.exceptions.ParseError:
    print("BUG: ParseError leaked through!")
```

## Why This Is A Bug

The `query` function's exception handling catches only `(LexerError, TypeError, UnicodeError)` but not `ParseError`. This violates the function's contract which states it should raise `InvalidEnvelopeExpressionError` when "Failed to unwrap event from envelope using expression". Users expect consistent exception handling for all JMESPath parsing failures.

## Fix

```diff
--- a/aws_lambda_powertools/utilities/jmespath_utils/__init__.py
+++ b/aws_lambda_powertools/utilities/jmespath_utils/__init__.py
@@ -15,7 +15,7 @@ from typing import Any
 
 import jmespath
-from jmespath.exceptions import LexerError
+from jmespath.exceptions import LexerError, ParseError
 from jmespath.functions import Functions, signature
 from typing_extensions import deprecated
 
@@ -84,7 +84,7 @@ def query(data: dict | str, envelope: str, jmespath_options: dict | None = None
     try:
         logger.debug(f"Envelope detected: {envelope}. JMESPath options: {jmespath_options}")
         return jmespath.search(envelope, data, options=jmespath.Options(**jmespath_options))
-    except (LexerError, TypeError, UnicodeError) as e:
+    except (LexerError, ParseError, TypeError, UnicodeError) as e:
         message = f"Failed to unwrap event from envelope using expression. Error: {e} Exp: {envelope}, Data: {data}"  # noqa: B306, E501
         raise InvalidEnvelopeExpressionError(message)
```