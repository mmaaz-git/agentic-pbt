"""Minimal reproduction of GetJsonSchemaHandler.mode attribute bug"""

from pydantic.annotated_handlers import GetJsonSchemaHandler

# According to the docstring:
# "Handler to call into the next JSON schema generation function.
#  Attributes:
#      mode: Json schema mode, can be `validation` or `serialization`."

# Create an instance
handler = GetJsonSchemaHandler()

# Try to access the documented 'mode' attribute
try:
    print(f"Mode value: {handler.mode}")
except AttributeError as e:
    print(f"ERROR: {e}")
    print("\nThis violates the documented contract that 'mode' is an attribute of GetJsonSchemaHandler")