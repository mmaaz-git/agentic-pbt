from click.globals import get_current_context, _local, push_context, pop_context
from click.core import Context, Command
import pytest

# Clear any existing context
while get_current_context(silent=True) is not None:
    try:
        pop_context()
    except:
        break

# Test 1: Set stack to a string (non-list)
_local.stack = "not_a_list"

# This should raise RuntimeError but doesn't
try:
    result = get_current_context(silent=False)
    print(f"Test 1 - No exception raised! Returned: {result}")
    print(f"Type of result: {type(result)}")
except RuntimeError as e:
    print(f"Test 1 - RuntimeError raised as expected: {e}")
except Exception as e:
    print(f"Test 1 - Different exception raised: {type(e).__name__}: {e}")

# Reset
_local.stack = []

# Test 2: What about other non-list types?
test_values = [
    42,
    3.14,
    {"key": "value"},
    None,
    True,
]

for value in test_values:
    _local.stack = value
    try:
        result = get_current_context(silent=False)
        print(f"Value {value} ({type(value).__name__}) - No exception raised! Returned: {result}")
    except RuntimeError as e:
        print(f"Value {value} ({type(value).__name__}) - RuntimeError raised: {e}")
    except Exception as e:
        print(f"Value {value} ({type(value).__name__}) - {type(e).__name__}: {e}")

# Clean up
_local.stack = []