import pydantic.typing

# This should handle non-existent modules gracefully
wrapper = pydantic.typing.getattr_migration('nonexistent.module')

# Try to access an attribute
try:
    result = wrapper('some_attr')
    print(f"Got result: {result}")
except AttributeError as e:
    print(f"AttributeError (expected): {e}")
except KeyError as e:
    print(f"KeyError (BUG!): {e}")
except Exception as e:
    print(f"Other error: {type(e).__name__}: {e}")