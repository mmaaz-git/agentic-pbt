"""Inspect the connection object returned by StaticPool"""
from sqlalchemy.pool import StaticPool


class FakeConnection:
    def __init__(self, id):
        self.id = id
        self.closed = False
    
    def close(self):
        self.closed = True
        
    def rollback(self):
        pass

connection_count = 0
def create_connection():
    global connection_count
    connection_count += 1
    return FakeConnection(connection_count)


pool = StaticPool(create_connection)
conn = pool.connect()

print(f"Type of conn: {type(conn)}")
print(f"Attributes of conn:")
for attr in dir(conn):
    if not attr.startswith('__'):
        print(f"  {attr}")

# Try to get the actual connection
print(f"\nTrying different attributes:")
if hasattr(conn, 'connection'):
    print(f"conn.connection: {conn.connection}")
if hasattr(conn, 'dbapi_connection'):
    print(f"conn.dbapi_connection: {conn.dbapi_connection}")
    print(f"conn.dbapi_connection.id: {conn.dbapi_connection.id}")
if hasattr(conn, '_dbapi_connection'):
    print(f"conn._dbapi_connection: {conn._dbapi_connection}")

# Get multiple connections and check if underlying is same
conn2 = pool.connect()
if hasattr(conn, 'dbapi_connection') and hasattr(conn2, 'dbapi_connection'):
    print(f"\nconn.dbapi_connection is conn2.dbapi_connection: {conn.dbapi_connection is conn2.dbapi_connection}")
    print(f"conn.dbapi_connection.id: {conn.dbapi_connection.id}")
    print(f"conn2.dbapi_connection.id: {conn2.dbapi_connection.id}")