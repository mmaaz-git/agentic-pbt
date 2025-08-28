"""Property-based tests for AsyncAdapt_aioodbc_cursor in sqlalchemy.connectors.aioodbc"""

from collections import deque
from unittest.mock import Mock
from hypothesis import given, strategies as st, settings, assume
import sqlalchemy.connectors.aioodbc as aioodbc_connector


class TestAsyncAdaptCursor:
    """Test AsyncAdapt_aioodbc_cursor properties"""
    
    def create_cursor(self, rows):
        """Helper to create a properly mocked cursor"""
        # Mock the connection
        mock_conn = Mock()
        mock_conn._connection = Mock()
        mock_conn.await_ = lambda x: x  # Simple passthrough for sync testing
        
        # Create cursor with mock connection
        cursor = aioodbc_connector.AsyncAdapt_aioodbc_cursor(mock_conn)
        cursor._rows = deque(rows)
        cursor.server_side = False
        cursor.arraysize = 1
        return cursor
    
    @given(st.lists(st.integers()))
    def test_fetchone_fetchall_consistency(self, rows):
        """Test that fetchone and fetchall work consistently.
        
        Properties:
        1. fetchone returns rows in order, one at a time
        2. fetchall returns all remaining rows
        3. After fetchall, fetchone returns None
        """
        # Create cursor with mocked rows
        cursor = self.create_cursor(rows)
        
        # Property 1: fetchone returns rows in order
        fetched = []
        for expected in rows:
            result = cursor.fetchone()
            assert result == expected
            fetched.append(result)
        
        # After fetching all, fetchone should return None
        assert cursor.fetchone() is None
        
        # Reset for next test
        cursor._rows = deque(rows)
        
        # Property 2: fetchall returns all rows
        all_rows = cursor.fetchall()
        assert all_rows == rows
        
        # Property 3: After fetchall, fetchone returns None
        assert cursor.fetchone() is None
        
        # Also, fetchall on empty should return empty list
        assert cursor.fetchall() == []
    
    @given(st.lists(st.integers(), min_size=1), st.integers(min_value=0))
    def test_fetchmany_properties(self, rows, size):
        """Test fetchmany behavior.
        
        Properties:
        1. fetchmany(n) returns at most n rows
        2. fetchmany returns rows in order
        3. Repeated fetchmany calls eventually exhaust all rows
        """
        cursor = self.create_cursor(rows)
        
        if size == 0:
            # fetchmany(0) should return empty list
            result = cursor.fetchmany(size)
            assert result == []
            # Rows should still be there
            assert len(cursor._rows) == len(rows)
        else:
            result = cursor.fetchmany(size)
            
            # Property 1: Returns at most size rows
            assert len(result) <= size
            
            # Property 2: Returns exact number if available
            expected_count = min(size, len(rows))
            assert len(result) == expected_count
            
            # Property 3: Returns rows in order
            assert result == rows[:expected_count]
            
            # Remaining rows should be correct
            assert list(cursor._rows) == rows[expected_count:]
    
    @given(st.lists(st.integers(), min_size=1))
    def test_fetchmany_default_size(self, rows):
        """Test fetchmany with default size (arraysize).
        
        Property: fetchmany() without size uses cursor.arraysize
        """
        cursor = self.create_cursor(rows)
        cursor.arraysize = 3  # Set a specific arraysize
        
        result = cursor.fetchmany()  # No size specified
        
        # Should fetch arraysize rows or all remaining
        expected_count = min(cursor.arraysize, len(rows))
        assert len(result) == expected_count
        assert result == rows[:expected_count]
    
    @given(st.lists(st.integers()))
    def test_fetch_operations_interaction(self, rows):
        """Test interaction between different fetch operations.
        
        Properties:
        1. fetchone + fetchall = all rows
        2. fetchmany + fetchall = all rows
        3. Mixed operations maintain order
        """
        if len(rows) < 3:
            return  # Need at least 3 rows for meaningful test
            
        # Test 1: fetchone + fetchall
        cursor = self.create_cursor(rows)
        
        first = cursor.fetchone()
        rest = cursor.fetchall()
        
        assert first == rows[0]
        assert rest == rows[1:]
        assert [first] + rest == rows
        
        # Test 2: fetchmany + fetchall
        cursor._rows = deque(rows)
        
        first_batch = cursor.fetchmany(2)
        remaining = cursor.fetchall()
        
        assert first_batch == rows[:2]
        assert remaining == rows[2:]
        assert first_batch + remaining == rows
    
    @given(st.lists(st.integers(), min_size=10))
    @settings(max_examples=200)
    def test_fetchmany_exhaustion(self, rows):
        """Test that repeated fetchmany eventually returns all rows exactly once.
        
        Property: Repeated fetchmany(n) calls return all rows exactly once
        """
        cursor = self.create_cursor(rows)
        
        collected = []
        batch_size = 3
        
        # Keep fetching until exhausted
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break
            collected.extend(batch)
        
        # Should have fetched all rows exactly once
        assert collected == rows
        
        # Further calls should return empty
        assert cursor.fetchmany(1) == []
        assert cursor.fetchone() is None
        assert cursor.fetchall() == []