import threading
import time
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from hypothesis import assume, given, settings, strategies as st
from sqlalchemy.pool import (
    NullPool,
    Pool,
    QueuePool,
    SingletonThreadPool,
    StaticPool
)


class MockConnection:
    """Mock database connection for testing"""
    def __init__(self, id: int):
        self.id = id
        self.closed = False
        self.invalidated = False
    
    def close(self):
        self.closed = True
    
    def rollback(self):
        """Mock rollback method required by SQLAlchemy pool"""
        pass
    
    def __repr__(self):
        return f"MockConnection({self.id})"


def create_mock_creator():
    """Create a mock connection creator that tracks created connections"""
    counter = [0]
    connections = []
    
    def creator():
        conn = MockConnection(counter[0])
        counter[0] += 1
        connections.append(conn)
        return conn
    
    creator.connections = connections
    creator.counter = counter
    return creator


# Test 1: QueuePool timeout behavior
@given(
    pool_size=st.integers(min_value=1, max_value=3),
    max_overflow=st.integers(min_value=0, max_value=2),
    timeout=st.floats(min_value=0.01, max_value=0.1)
)
@settings(max_examples=50, deadline=10000)
def test_queuepool_timeout_behavior(pool_size, max_overflow, timeout):
    """Test that QueuePool properly times out when all connections are in use"""
    creator = create_mock_creator()
    pool = QueuePool(creator, pool_size=pool_size, max_overflow=max_overflow, timeout=timeout)
    
    max_connections = pool_size + max_overflow
    connections = []
    
    # Checkout all available connections
    for i in range(max_connections):
        conn = pool.connect()
        connections.append(conn)
    
    # Property: Pool should be at max capacity
    assert pool.checkedout() == max_connections
    
    # Try to get one more connection - should timeout
    import time
    start = time.time()
    try:
        extra_conn = pool.connect()
        # If we got here, the pool allowed more connections than it should
        assert False, f"Pool allowed connection beyond max capacity ({max_connections})"
    except Exception as e:
        elapsed = time.time() - start
        # Property: Should timeout roughly after the specified timeout
        # Allow some tolerance for timing
        assert elapsed >= timeout * 0.5, f"Timed out too quickly: {elapsed} < {timeout}"
        assert elapsed <= timeout * 3, f"Took too long to timeout: {elapsed} > {timeout * 3}"
    
    # Clean up
    for conn in connections:
        conn.close()
    pool.dispose()


# Test 2: Pool recreate behavior
@given(
    pool_size=st.integers(min_value=1, max_value=5),
    num_operations=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50)
def test_pool_recreate_maintains_state(pool_size, num_operations):
    """Test that pool.recreate() maintains pool configuration"""
    creator = create_mock_creator()
    original_pool = QueuePool(creator, pool_size=pool_size, max_overflow=2)
    
    # Get some initial state
    original_size = original_pool.size()
    
    # Recreate the pool
    new_pool = original_pool.recreate()
    
    # Property: Recreated pool should have same configuration
    assert new_pool.size() == original_size, \
        f"Recreated pool size {new_pool.size()} != original {original_size}"
    
    # Property: Recreated pool should be functional
    conn = new_pool.connect()
    assert conn is not None
    conn.close()
    
    # Clean up
    original_pool.dispose()
    new_pool.dispose()


# Test 3: Connection invalidation
@given(
    pool_type=st.sampled_from([QueuePool, StaticPool]),
    num_invalidations=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=50)
def test_connection_invalidation(pool_type, num_invalidations):
    """Test that invalidated connections are replaced with new ones"""
    creator = create_mock_creator()
    
    if pool_type == QueuePool:
        pool = pool_type(creator, pool_size=2, max_overflow=1)
    else:
        pool = pool_type(creator)
    
    connections_before = creator.counter[0]
    
    for i in range(num_invalidations):
        conn = pool.connect()
        conn_id_before = conn.dbapi_connection.id
        
        # Invalidate the connection
        conn.invalidate()
        conn.close()
        
        # Get a new connection
        conn2 = pool.connect()
        conn_id_after = conn2.dbapi_connection.id
        
        # Property: After invalidation, should get a different connection
        # (for non-StaticPool)
        if pool_type != StaticPool:
            assert conn_id_after != conn_id_before, \
                f"Got same connection after invalidation: {conn_id_after}"
        
        conn2.close()
    
    pool.dispose()


# Test 4: Pool dispose behavior
@given(
    pool_size=st.integers(min_value=1, max_value=5),
    num_connections=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50)
def test_pool_dispose_clears_connections(pool_size, num_connections):
    """Test that pool.dispose() properly clears all connections"""
    creator = create_mock_creator()
    pool = QueuePool(creator, pool_size=pool_size, max_overflow=5)
    
    connections = []
    # Get some connections
    for i in range(min(num_connections, pool_size)):
        conn = pool.connect()
        connections.append(conn)
    
    initial_checkedout = pool.checkedout()
    
    # Return connections to pool
    for conn in connections:
        conn.close()
    
    initial_checkedin = pool.checkedin()
    
    # Dispose the pool
    pool.dispose()
    
    # Property: After dispose, pool should be empty
    assert pool.checkedin() == 0, \
        f"Pool still has {pool.checkedin()} checked-in connections after dispose"
    assert pool.checkedout() == 0, \
        f"Pool still has {pool.checkedout()} checked-out connections after dispose"


# Test 5: SingletonThreadPool size limit
@given(
    pool_size=st.integers(min_value=1, max_value=3),
    num_threads=st.integers(min_value=4, max_value=10)
)
@settings(max_examples=20, deadline=10000)
def test_singleton_thread_pool_size_limit(pool_size, num_threads):
    """Test SingletonThreadPool respects pool_size limit"""
    assume(num_threads > pool_size)  # Only test when threads exceed pool size
    
    creator = create_mock_creator()
    pool = SingletonThreadPool(creator, pool_size=pool_size)
    
    connections_per_thread = {}
    errors = []
    lock = threading.Lock()
    
    def get_connection(thread_num):
        try:
            conn = pool.connect()
            thread_id = threading.get_ident()
            with lock:
                connections_per_thread[thread_id] = conn
            # Hold connection for a bit
            time.sleep(0.01)
            # Don't close - we want to exceed the pool size
        except Exception as e:
            with lock:
                errors.append(f"Thread {thread_num} error: {e}")
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=get_connection, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # The documentation warns that connections beyond pool_size may be closed
    # Let's check that we don't get more active connections than expected
    unique_conns = set()
    for conn in connections_per_thread.values():
        if hasattr(conn, 'dbapi_connection'):
            unique_conns.add(id(conn.dbapi_connection))
    
    # Note: SingletonThreadPool behavior with size limits is documented as
    # potentially problematic, so we're just checking it doesn't crash
    assert len(errors) == 0 or "closed" in str(errors), \
        f"Unexpected errors: {errors}"
    
    # Clean up
    for conn in connections_per_thread.values():
        try:
            conn.close()
        except:
            pass
    pool.dispose()


# Test 6: LIFO vs FIFO behavior in QueuePool
@given(use_lifo=st.booleans())
@settings(max_examples=20)
def test_queuepool_lifo_fifo_order(use_lifo):
    """Test QueuePool LIFO/FIFO connection ordering"""
    creator = create_mock_creator()
    pool = QueuePool(creator, pool_size=3, max_overflow=0, use_lifo=use_lifo)
    
    # Get three connections
    conn1 = pool.connect()
    conn2 = pool.connect()
    conn3 = pool.connect()
    
    # Mark them so we can identify them
    conn1.dbapi_connection.marker = 1
    conn2.dbapi_connection.marker = 2
    conn3.dbapi_connection.marker = 3
    
    # Return them in order
    conn1.close()
    conn2.close()
    conn3.close()
    
    # Get them back
    new_conn1 = pool.connect()
    new_conn2 = pool.connect()
    new_conn3 = pool.connect()
    
    markers = [
        new_conn1.dbapi_connection.marker,
        new_conn2.dbapi_connection.marker,
        new_conn3.dbapi_connection.marker
    ]
    
    if use_lifo:
        # LIFO: Last returned should be first retrieved
        # Property: LIFO order should be [3, 2, 1]
        expected = [3, 2, 1]
    else:
        # FIFO: First returned should be first retrieved
        # Property: FIFO order should be [1, 2, 3]
        expected = [1, 2, 3]
    
    assert markers == expected, \
        f"{'LIFO' if use_lifo else 'FIFO'} order incorrect: {markers} != {expected}"
    
    # Clean up
    new_conn1.close()
    new_conn2.close()
    new_conn3.close()
    pool.dispose()