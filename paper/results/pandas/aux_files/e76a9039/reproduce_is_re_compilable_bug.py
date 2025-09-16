import pandas.api.types as types

invalid_patterns = [
    '[',       # Unterminated character set
    '(',       # Unterminated group
    '*',       # Nothing to repeat
    '(?P<',    # Unterminated named group
    '\\',      # Escape at end of pattern
]

for pattern in invalid_patterns:
    print(f"Testing is_re_compilable('{pattern}')")
    try:
        result = types.is_re_compilable(pattern)
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}")
    print()