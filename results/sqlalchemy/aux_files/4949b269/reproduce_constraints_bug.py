"""
Investigate the return type of sort_tables_and_constraints
"""
from sqlalchemy import MetaData, Table, Column, Integer, String
from sqlalchemy.schema import sort_tables_and_constraints

# Create simple tables with no dependencies
metadata = MetaData()
table_a = Table('a', metadata,
    Column('id', Integer, primary_key=True),
    Column('data', String(50))
)
table_b = Table('b', metadata,
    Column('id', Integer, primary_key=True),
    Column('data', String(50))
)

# Test the return structure
result = sort_tables_and_constraints([table_a, table_b])

print("Testing sort_tables_and_constraints return structure:")
print("=" * 60)
print(f"Result type: {type(result)}")
print(f"Number of items: {len(result)}")
print()

for i, item in enumerate(result):
    print(f"Item {i}:")
    print(f"  Type: {type(item)}")
    print(f"  Length: {len(item)}")
    
    table, constraints = item
    print(f"  Table: {table.name if table is not None else None}")
    print(f"  Constraints type: {type(constraints)}")
    print(f"  Constraints value: {constraints}")
    print()

# Check if the docstring claims it returns lists
import sqlalchemy.schema
print("\nDocstring excerpt about return type:")
print("=" * 60)
doc = sqlalchemy.schema.sort_tables_and_constraints.__doc__
# Find the part about return type
lines = doc.split('\n')
for i, line in enumerate(lines):
    if 'tuple' in line.lower() or 'return' in line.lower():
        # Print context around this line
        start = max(0, i-1)
        end = min(len(lines), i+3)
        for j in range(start, end):
            print(lines[j])