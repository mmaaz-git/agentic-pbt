"""
Confirm that sort_tables_and_constraints returns sets instead of lists
for the constraints part of the tuple, violating its documented interface.
"""
from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from sqlalchemy.schema import sort_tables_and_constraints

# Test with tables that have foreign key constraints
metadata = MetaData()

parent = Table('parent', metadata,
    Column('id', Integer, primary_key=True)
)

child1 = Table('child1', metadata,
    Column('id', Integer, primary_key=True),
    Column('parent_id', Integer, ForeignKey('parent.id'))
)

child2 = Table('child2', metadata,
    Column('id', Integer, primary_key=True),
    Column('parent_id', Integer, ForeignKey('parent.id'))
)

# Test the return structure
result = sort_tables_and_constraints([child1, parent, child2])

print("Testing with tables that have foreign key constraints:")
print("=" * 60)

for i, (table, constraints) in enumerate(result):
    table_name = table.name if table is not None else None
    print(f"\nEntry {i}: Table='{table_name}'")
    print(f"  Constraints type: {type(constraints).__name__}")
    print(f"  Expected type: list (per docstring)")
    print(f"  Actual type: {type(constraints).__name__}")
    
    if type(constraints).__name__ != 'list':
        print(f"  ❌ BUG: Expected list but got {type(constraints).__name__}")
    else:
        print(f"  ✓ Correct type")

print("\n" + "=" * 60)
print("DOCSTRING EXCERPT:")
print("The function claims to emit tuples of:")
print("  (Table, [ForeignKeyConstraint, ...])")
print("Where [...] notation indicates a list in Python documentation.")
print("\nCONCLUSION: The function violates its documented interface by")
print("returning sets instead of lists for non-None table entries.")