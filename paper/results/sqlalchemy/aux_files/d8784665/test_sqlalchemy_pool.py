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


# Test 1: QueuePool size invariants
@given(
    pool_size=st.integers(min_value=1, max_value=10),
    max_overflow=st.integers(min_value=0, max_value=10),
    num_checkouts=st.integers(min_value=0, max_value=30)
)
@settings(max_examples=100)
def test_queuepool_size_invariants(pool_size, max_overflow, num_checkouts):
    """Test that QueuePool respects its size and overflow limits"""
    creator = create_mock_creator()
    pool = QueuePool(creator, pool_size=pool_size, max_overflow=max_overflow, timeout=0.1)
    
    connections = []
    max_allowed = pool_size + max_overflow
    
    # Try to checkout connections up to num_checkouts
    for i in range(num_checkouts):
        try:
            conn = pool.connect()
            connections.append(conn)
            
            # Property: checkedout should never exceed pool_size + max_overflow
            assert pool.checkedout() <= max_allowed, \
                f"checkedout {pool.checkedout()} exceeds max_allowed {max_allowed}"
            
            # Property: checkedout + checkedin should be <= pool_size + max_overflow
            total = pool.checkedout() + pool.checkedin()
            assert total <= max_allowed, \
                f"total connections {total} exceeds max_allowed {max_allowed}"
                
        except Exception as e:
            # If we get an exception, it should be because we've hit the limit
            if i < max_allowed:
                # We shouldn't get an exception before hitting the limit
                raise AssertionError(f"Got exception at connection {i+1} but limit is {max_allowed}: {e}")
            break
    
    # Clean up
    for conn in connections:
        conn.close()
    pool.dispose()


# Test 2: SingletonThreadPool thread isolation
@given(
    pool_size=st.integers(min_value=1, max_value=5),
    num_threads=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50, deadline=5000)
def test_singleton_thread_pool_isolation(pool_size, num_threads):
    """Test that SingletonThreadPool provides one connection per thread"""
    creator = create_mock_creator()
    pool = SingletonThreadPool(creator, pool_size=pool_size)
    
    thread_connections: Dict[int, Any] = {}
    errors = []
    
    def get_connection():
        try:
            conn = pool.connect()
            thread_id = threading.get_ident()
            
            if thread_id not in thread_connections:
                thread_connections[thread_id] = conn
            else:
                # Property: Same thread should get same connection
                if thread_connections[thread_id] is not conn:
                    errors.append(f"Thread {thread_id} got different connection")
            
            # Small delay to ensure threads overlap
            time.sleep(0.001)
            conn.close()
        except Exception as e:
            errors.append(f"Thread error: {e}")
    
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=get_connection)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Check for errors
    assert not errors, f"Thread isolation errors: {errors}"
    
    # Property: Each thread should have gotten a unique connection
    # (up to pool_size limit)
    unique_connections = set()
    for conn in thread_connections.values():
        if hasattr(conn, '_connection'):
            unique_connections.add(id(conn._connection))
    
    pool.dispose()


# Test 3: NullPool non-pooling behavior
@given(num_connections=st.integers(min_value=1, max_value=20))
@settings(max_examples=100)
def test_nullpool_creates_new_connections(num_connections):
    """Test that NullPool always creates new connections"""
    creator = create_mock_creator()
    pool = NullPool(creator)
    
    connection_ids = []
    
    for i in range(num_connections):
        conn = pool.connect()
        # Get the underlying connection ID
        if hasattr(conn, 'dbapi_connection'):
            conn_id = conn.dbapi_connection.id
        elif hasattr(conn, '_connection'):
            conn_id = conn._connection.id
        else:
            # Fallback for different internal structures
            conn_id = id(conn)
        
        # Property: NullPool should create a new connection every time
        assert conn_id not in connection_ids, \
            f"NullPool reused connection {conn_id} at iteration {i}"
        
        connection_ids.append(conn_id)
        conn.close()
    
    # Property: Number of unique connections should equal num_connections
    assert len(set(connection_ids)) == num_connections, \
        f"Expected {num_connections} unique connections, got {len(set(connection_ids))}"
    
    pool.dispose()


# Test 4: StaticPool singleton behavior
@given(num_connections=st.integers(min_value=2, max_value=20))
@settings(max_examples=100)
def test_staticpool_singleton_behavior(num_connections):
    """Test that StaticPool maintains exactly one connection"""
    creator = create_mock_creator()
    pool = StaticPool(creator)
    
    connections = []
    connection_ids = []
    
    for i in range(num_connections):
        conn = pool.connect()
        connections.append(conn)
        
        # Get the underlying connection - use dbapi_connection which is the actual connection
        if hasattr(conn, 'dbapi_connection'):
            conn_id = id(conn.dbapi_connection)
        elif hasattr(conn, '_connection'):
            conn_id = id(conn._connection)
        else:
            conn_id = id(conn)
        
        connection_ids.append(conn_id)
    
    # Property: All connections should be the same (singleton)
    unique_ids = set(connection_ids)
    assert len(unique_ids) == 1, \
        f"StaticPool created {len(unique_ids)} different connections, expected 1"
    
    # Clean up
    for conn in connections:
        conn.close()
    pool.dispose()


# Test 5: QueuePool overflow calculation
@given(
    pool_size=st.integers(min_value=1, max_value=10),
    max_overflow=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100)
def test_queuepool_overflow_calculation(pool_size, max_overflow):
    """Test QueuePool overflow calculation remains consistent"""
    creator = create_mock_creator()
    pool = QueuePool(creator, pool_size=pool_size, max_overflow=max_overflow)
    
    # Initial state
    initial_overflow = pool.overflow()
    
    # Property: overflow should start at negative pool_size
    assert initial_overflow == -pool_size, \
        f"Initial overflow {initial_overflow} != -{pool_size}"
    
    connections = []
    
    # Checkout connections up to pool_size
    for i in range(min(pool_size, 5)):  # Limit to avoid too many connections
        conn = pool.connect()
        connections.append(conn)
        
        # Property: overflow should increase as we checkout beyond pool
        current_overflow = pool.overflow()
        expected_overflow = -pool_size + pool.checkedout()
        assert current_overflow == expected_overflow, \
            f"Overflow {current_overflow} != expected {expected_overflow}"
    
    # Clean up
    for conn in connections:
        conn.close()
    pool.dispose()


# Test 6: Pool status string format
@given(
    pool_size=st.integers(min_value=1, max_value=5),
    max_overflow=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=50)
def test_queuepool_status_format(pool_size, max_overflow):
    """Test that QueuePool.status() returns properly formatted string"""
    creator = create_mock_creator()
    pool = QueuePool(creator, pool_size=pool_size, max_overflow=max_overflow)
    
    status = pool.status()
    
    # Property: status should be a string containing size information
    assert isinstance(status, str), f"Status should be string, got {type(status)}"
    assert "Pool size:" in status, f"Status missing 'Pool size:' in {status}"
    assert "Connections in pool:" in status, f"Status missing 'Connections in pool:' in {status}"
    
    # Property: status should contain valid numbers
    import re
    numbers = re.findall(r'\d+', status)
    assert len(numbers) >= 2, f"Status should contain at least 2 numbers, found {len(numbers)}"
    
    pool.dispose()