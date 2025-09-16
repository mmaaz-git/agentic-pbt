"""Minimal reproduction of StaticPool behavior"""
from sqlalchemy.pool import StaticPool


# Create a simple connection creator
connection_count = 0
def create_connection():
    global connection_count
    connection_count += 1
    return f"Connection_{connection_count}"


# Test StaticPool behavior
pool = StaticPool(create_connection, reset_on_return=False)

# Get multiple connections
conn1 = pool.connect()
conn2 = pool.connect()

print(f"conn1: {conn1}")
print(f"conn2: {conn2}")
print(f"conn1 is conn2: {conn1 is conn2}")
print(f"ID of conn1: {id(conn1)}")
print(f"ID of conn2: {id(conn2)}")

# Check underlying connections
if hasattr(conn1, '_connection'):
    print(f"conn1._connection: {conn1._connection}")
    print(f"conn2._connection: {conn2._connection}")
    print(f"conn1._connection is conn2._connection: {conn1._connection is conn2._connection}")

print(f"\nTotal connections created: {connection_count}")

# What does the docstring say?
print("\nStaticPool docstring:")
print(StaticPool.__doc__)