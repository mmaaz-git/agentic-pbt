"""Minimal reproduction of the PostgreSQL FLOAT array bug."""

from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import psycopg2 as pg_dialect

# Create a FLOAT array type
array_type = postgresql.ARRAY(postgresql.FLOAT)
dialect = pg_dialect.dialect()

# Get processors
bind_processor = array_type.bind_processor(dialect)
result_processor = array_type.result_processor(dialect, None)

print(f"Bind processor: {bind_processor}")
print(f"Result processor: {result_processor}")

# This should work but fails
data = []  # Empty array
print(f"\nTesting with empty array: {data}")

try:
    if bind_processor:
        bound = bind_processor(data)
        print(f"After bind: {bound}")
    
    if result_processor:
        result = result_processor(bound)
        print(f"After result: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Test with non-empty array
data = [1.5, 2.5, 3.5]
print(f"\nTesting with non-empty array: {data}")

try:
    if bind_processor:
        bound = bind_processor(data)
        print(f"After bind: {bound}")
    
    if result_processor:
        result = result_processor(bound)
        print(f"After result: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")