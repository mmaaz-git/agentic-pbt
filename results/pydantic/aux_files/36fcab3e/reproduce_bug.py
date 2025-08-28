"""Minimal reproduction of the import_string bug."""

from pydantic._internal._validators import import_string

# These should all raise PydanticCustomError, but some raise TypeError instead
test_cases = [
    '.',     # Relative import - raises TypeError
    '..',    # Parent relative import - raises TypeError  
    '../',   # Parent relative with slash - raises TypeError
    './',    # Current relative with slash - raises TypeError
]

for case in test_cases:
    try:
        result = import_string(case)
        print(f"✓ {case!r}: {result}")
    except Exception as e:
        error_type = type(e).__name__
        if error_type != 'PydanticCustomError':
            print(f"✗ {case!r}: Expected PydanticCustomError, got {error_type}: {e}")
        else:
            print(f"✓ {case!r}: Correctly raised PydanticCustomError")