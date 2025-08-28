from click.globals import get_current_context, _local

# Clear any existing context
_local.stack = []

# Simulate corruption: stack becomes a string instead of list
# This could happen if external code incorrectly manipulates thread-local storage
_local.stack = "corrupted"

# Expected: RuntimeError("There is no active click context.")
# Actual: Returns 'd' (last character of the string)
try:
    result = get_current_context(silent=False)
    print(f"BUG: get_current_context returned '{result}' instead of raising RuntimeError")
    print(f"Type: {type(result)}")
except RuntimeError as e:
    print(f"Correctly raised RuntimeError: {e}")