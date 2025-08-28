"""Check if StaticPool reuses the underlying connection"""
from sqlalchemy.pool import StaticPool


# Create a simple connection creator that returns unique objects
class FakeConnection:
    def __init__(self, id):
        self.id = id
        self.closed = False
    
    def close(self):
        self.closed = True
        
    def rollback(self):
        pass  # Add rollback to avoid errors

connection_count = 0
def create_connection():
    global connection_count
    connection_count += 1
    return FakeConnection(connection_count)


# Test StaticPool behavior
pool = StaticPool(create_connection)

# Get multiple connections
conn1 = pool.connect()
conn2 = pool.connect()
conn3 = pool.connect()

print(f"Wrapper objects are different: {conn1 is not conn2}")
print(f"conn1 ID: {id(conn1)}, conn2 ID: {id(conn2)}, conn3 ID: {id(conn3)}")

# Check underlying connections
if hasattr(conn1, '_connection'):
    print(f"\nUnderlying connections:")
    print(f"conn1._connection.id: {conn1._connection.id}")
    print(f"conn2._connection.id: {conn2._connection.id}")
    print(f"conn3._connection.id: {conn3._connection.id}")
    print(f"All underlying connections are the same: {conn1._connection is conn2._connection is conn3._connection}")

print(f"\nTotal connections created by creator function: {connection_count}")

# Let's also check what happens when we close and reopen
conn1.close()
conn4 = pool.connect()
if hasattr(conn4, '_connection'):
    print(f"\nAfter closing conn1 and getting conn4:")
    print(f"conn4._connection.id: {conn4._connection.id}")
    print(f"conn4 uses same underlying connection: {conn4._connection is conn2._connection}")