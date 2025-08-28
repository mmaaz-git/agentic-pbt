"""
Minimal reproduction of the non-deterministic behavior in sort_tables
"""
import random
from sqlalchemy import MetaData, Table, Column, Integer, String
from sqlalchemy.schema import sort_tables

# Create two independent tables with no dependencies
metadata = MetaData()
table_a = Table('a', metadata,
    Column('id', Integer, primary_key=True),
    Column('data', String(50))
)
table_b = Table('b', metadata,
    Column('id', Integer, primary_key=True),
    Column('data', String(50))  
)

# Test determinism by sorting the same tables multiple times
print("Testing determinism of sort_tables with independent tables:")
print("=" * 60)

results = []
for run in range(10):
    # Shuffle the input randomly each time
    tables = [table_a, table_b]
    random.shuffle(tables)
    
    # Sort the tables
    sorted_tables = sort_tables(tables)
    result = [t.name for t in sorted_tables]
    results.append(result)
    
    input_order = [t.name for t in tables]
    print(f"Run {run + 1}: Input order: {str(input_order):15} → Output: {result}")

# Check if all results are the same
unique_results = list(set(tuple(r) for r in results))
print(f"\nUnique results: {unique_results}")

if len(unique_results) > 1:
    print("\n❌ BUG CONFIRMED: sort_tables is non-deterministic!")
    print("   The function returns different orderings for the same logical input.")
else:
    print("\n✓ Function appears deterministic in this test")