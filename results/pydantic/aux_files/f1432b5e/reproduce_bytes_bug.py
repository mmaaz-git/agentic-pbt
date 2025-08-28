"""Minimal reproduction of TypeAdapter bytes round-trip bug."""

from pydantic import TypeAdapter

# Create a TypeAdapter for bytes
ta = TypeAdapter(bytes)

# Test with non-UTF-8 bytes
non_utf8_bytes = b'\x80'  # Invalid UTF-8 sequence

# Step 1: TypeAdapter accepts these bytes
validated = ta.validate_python(non_utf8_bytes)
print(f"validate_python({non_utf8_bytes!r}) = {validated!r}")
assert validated == non_utf8_bytes

# Step 2: But cannot serialize them to JSON
try:
    json_output = ta.dump_json(validated)
    print(f"dump_json succeeded: {json_output}")
except Exception as e:
    print(f"dump_json FAILED: {e}")
    print("\nThis violates the round-trip property!")
    print("TypeAdapter accepts bytes that it cannot serialize.")
    
# The round-trip property states that for any valid input x:
# validate_json(dump_json(x)) should equal x
# But here, dump_json fails even though x was accepted by validate_python