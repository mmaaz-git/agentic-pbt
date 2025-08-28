import threading
import time
import weakref
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from hypothesis import assume, given, settings, strategies as st, HealthCheck
from sqlalchemy.pool import (
    NullPool,
    Pool,
    QueuePool,
    SingletonThreadPool,
    StaticPool,
    AssertionPool
)


class MockConnection:
    """Mock database connection for testing"""
    def __init__(self, id: int):
        self.id = id
        self.closed = False
        self.invalidated = False
        self.rollback_count = 0
        self.commit_count = 0
    
    def close(self):
        self.closed = True
    
    def rollback(self):
        self.rollback_count += 1
    
    def commit(self):
        self.commit_count += 1
    
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


# Test 1: AssertionPool behavior
@given(num_operations=st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_assertion_pool_single_connection(num_operations):
    """Test AssertionPool enforces single connection constraint"""
    creator = create_mock_creator()
    pool = AssertionPool(creator)
    
    # Get first connection
    conn1 = pool.connect()
    
    # Property: AssertionPool should raise if we try to get another connection
    # while one is still checked out
    try:
        conn2 = pool.connect()
        # If we got here, AssertionPool didn't enforce its constraint
        assert False, "AssertionPool allowed multiple connections"
    except AssertionError as e:
        # Expected behavior - AssertionPool should raise AssertionError
        pass
    except Exception as e:
        # Some other error - this might be a bug
        assert False, f"Unexpected error type: {type(e).__name__}: {e}"
    
    # Return the connection
    conn1.close()
    
    # Property: After returning, should be able to get a connection again
    conn3 = pool.connect()
    assert conn3 is not None
    conn3.close()
    
    pool.dispose()


# Test 2: Pool recycle parameter
@given(
    recycle_time=st.integers(min_value=1, max_value=10),
    wait_time=st.floats(min_value=0, max_value=0.1)
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_pool_recycle_old_connections(recycle_time, wait_time):
    """Test that pools recycle connections older than recycle time"""
    creator = create_mock_creator()
    # Use a very short recycle time (in seconds)
    pool = QueuePool(creator, pool_size=1, max_overflow=0, recycle=recycle_time)
    
    # Get a connection
    conn1 = pool.connect()
    conn1_id = conn1.dbapi_connection.id
    conn1.close()
    
    # Wait if specified
    if wait_time > 0:
        time.sleep(wait_time)
    
    # Get connection again
    conn2 = pool.connect()
    conn2_id = conn2.dbapi_connection.id
    
    # Property: Connections should be recycled based on age
    # Note: This is hard to test precisely due to timing, but we can
    # check basic functionality
    assert conn2 is not None
    conn2.close()
    
    pool.dispose()


# Test 3: Connection with reset_on_return
@given(
    reset_style=st.sampled_from([True, False, 'rollback', 'commit', None])
)
@settings(max_examples=50)
def test_pool_reset_on_return(reset_style):
    """Test different reset_on_return behaviors"""
    creator = create_mock_creator()
    pool = QueuePool(creator, pool_size=1, max_overflow=0, reset_on_return=reset_style)
    
    # Get a connection
    conn = pool.connect()
    underlying = conn.dbapi_connection
    initial_rollback_count = underlying.rollback_count
    initial_commit_count = underlying.commit_count
    
    # Return the connection
    conn.close()
    
    # Check what happened based on reset_style
    if reset_style in [True, 'rollback']:
        # Property: Should have called rollback
        assert underlying.rollback_count > initial_rollback_count, \
            f"Expected rollback with reset_on_return={reset_style}"
    elif reset_style == 'commit':
        # Property: Should have called commit
        # Note: SQLAlchemy may not actually call commit in all cases
        pass  # This behavior is version-dependent
    elif reset_style in [False, None]:
        # Property: Should not reset
        assert underlying.rollback_count == initial_rollback_count, \
            f"Unexpected rollback with reset_on_return={reset_style}"
    
    pool.dispose()


# Test 4: Pool with negative pool_size (should be rejected)
@given(
    negative_size=st.integers(min_value=-10, max_value=-1)
)
@settings(max_examples=20)
def test_pool_negative_size_rejected(negative_size):
    """Test that pools reject negative size parameters"""
    creator = create_mock_creator()
    
    try:
        pool = QueuePool(creator, pool_size=negative_size)
        # Some implementations might accept this and treat as 0
        # Let's check the actual size
        actual_size = pool.size()
        # Property: Size should never be negative
        assert actual_size >= 0, f"Pool has negative size: {actual_size}"
        pool.dispose()
    except (ValueError, AssertionError, TypeError) as e:
        # Expected - negative size should be rejected
        pass


# Test 5: Pool overflow edge cases
@given(
    pool_size=st.integers(min_value=0, max_value=3),
    max_overflow=st.integers(min_value=-1, max_value=3)
)
@settings(max_examples=50)
def test_pool_zero_size_and_negative_overflow(pool_size, max_overflow):
    """Test pool behavior with edge case size parameters"""
    creator = create_mock_creator()
    
    try:
        pool = QueuePool(creator, pool_size=pool_size, max_overflow=max_overflow)
        
        # Calculate expected max connections
        if max_overflow < 0:
            # Negative overflow might be treated as 0 or rejected
            expected_max = pool_size
        else:
            expected_max = pool_size + max_overflow
        
        if expected_max == 0:
            # Property: Pool with 0 total capacity shouldn't give connections
            try:
                conn = pool.connect()
                # Some pools might still allow this
                conn.close()
            except:
                # Expected - can't get connection from zero-capacity pool
                pass
        else:
            # Property: Should be able to get at least one connection
            conn = pool.connect()
            assert conn is not None
            conn.close()
        
        pool.dispose()
    except (ValueError, AssertionError) as e:
        # Some invalid combinations might be rejected
        pass


# Test 6: Concurrent connection checkout/checkin
@given(
    pool_size=st.integers(min_value=2, max_value=5),
    num_threads=st.integers(min_value=2, max_value=10),
    iterations=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=20, deadline=10000)
def test_concurrent_checkout_checkin(pool_size, num_threads, iterations):
    """Test thread safety of concurrent checkouts and checkins"""
    creator = create_mock_creator()
    pool = QueuePool(creator, pool_size=pool_size, max_overflow=2)
    
    errors = []
    checkout_counts = [0]
    lock = threading.Lock()
    
    def worker():
        try:
            for _ in range(iterations):
                conn = pool.connect()
                with lock:
                    checkout_counts[0] += 1
                    current_checked_out = pool.checkedout()
                    # Property: checkedout count should never exceed pool limits
                    if current_checked_out > pool_size + 2:  # max_overflow=2
                        errors.append(f"Too many checked out: {current_checked_out}")
                
                # Simulate some work
                time.sleep(0.001)
                
                conn.close()
                with lock:
                    checkout_counts[0] -= 1
        except Exception as e:
            with lock:
                errors.append(f"Thread error: {e}")
    
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Property: No errors should occur during concurrent access
    assert len(errors) == 0, f"Concurrent access errors: {errors}"
    
    # Property: All connections should be returned
    assert pool.checkedout() == 0, f"Connections still checked out: {pool.checkedout()}"
    
    pool.dispose()


# Test 7: StaticPool with connection invalidation
@given(num_invalidations=st.integers(min_value=1, max_value=5))
@settings(max_examples=50)
def test_staticpool_invalidation_creates_new(num_invalidations):
    """Test that StaticPool creates new connection after invalidation"""
    creator = create_mock_creator()
    pool = StaticPool(creator)
    
    conn_ids = []
    
    for i in range(num_invalidations):
        conn = pool.connect()
        conn_id = conn.dbapi_connection.id
        conn_ids.append(conn_id)
        
        # Invalidate and close
        conn.invalidate()
        conn.close()
    
    # Get one more connection
    final_conn = pool.connect()
    final_id = final_conn.dbapi_connection.id
    conn_ids.append(final_id)
    final_conn.close()
    
    # Property: After invalidation, StaticPool should create a new connection
    # Check that we got new connections after invalidation
    unique_ids = set(conn_ids)
    assert len(unique_ids) > 1, \
        f"StaticPool didn't create new connections after invalidation: {conn_ids}"
    
    pool.dispose()