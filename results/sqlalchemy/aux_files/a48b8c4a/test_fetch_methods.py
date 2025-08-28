"""Direct testing of fetch methods logic without complex initialization"""

from collections import deque
from hypothesis import given, strategies as st, settings


class MockCursor:
    """Simple mock cursor that implements the fetch logic directly"""
    
    def __init__(self, rows):
        self._rows = deque(rows)
        self.arraysize = 1
        
    def fetchone(self):
        """Direct implementation from AsyncAdapt_aioodbc_cursor"""
        if self._rows:
            return self._rows.popleft()
        else:
            return None
    
    def fetchall(self):
        """Direct implementation from AsyncAdapt_aioodbc_cursor"""
        retval = list(self._rows)
        self._rows.clear()
        return retval
    
    def fetchmany(self, size=None):
        """Direct implementation from AsyncAdapt_aioodbc_cursor"""
        if size is None:
            size = self.arraysize
        rr = self._rows
        return [rr.popleft() for _ in range(min(size, len(rr)))]


class TestFetchMethods:
    """Test the fetch methods logic"""
    
    @given(st.lists(st.integers()))
    def test_fetchone_returns_none_when_empty(self, initial_rows):
        """Property: fetchone returns None when no rows available"""
        cursor = MockCursor(initial_rows)
        
        # Fetch all rows
        for _ in initial_rows:
            cursor.fetchone()
        
        # Now should return None
        assert cursor.fetchone() is None
        assert cursor.fetchone() is None  # Should stay None
    
    @given(st.lists(st.integers(), min_size=1))
    def test_fetchall_clears_rows(self, rows):
        """Property: fetchall should clear all rows from internal storage"""
        cursor = MockCursor(rows)
        
        result = cursor.fetchall()
        assert result == rows
        
        # Internal rows should be empty
        assert len(cursor._rows) == 0
        
        # Further fetches should return empty/None
        assert cursor.fetchall() == []
        assert cursor.fetchone() is None
    
    @given(st.lists(st.integers(), min_size=5), st.integers(min_value=1, max_value=3))
    def test_fetchmany_partial_fetches(self, rows, size):
        """Property: fetchmany(n) removes exactly min(n, remaining) rows"""
        cursor = MockCursor(rows)
        
        initial_count = len(rows)
        result = cursor.fetchmany(size)
        
        # Should fetch exactly min(size, initial_count) rows
        expected_fetched = min(size, initial_count)
        assert len(result) == expected_fetched
        
        # Remaining rows should be correct
        assert len(cursor._rows) == initial_count - expected_fetched
        
        # The fetched rows should be the first ones
        assert result == rows[:expected_fetched]
        assert list(cursor._rows) == rows[expected_fetched:]
    
    @given(st.lists(st.integers()))
    @settings(max_examples=500)
    def test_fetchmany_zero_size(self, rows):
        """Property: fetchmany(0) should return empty list and not consume rows"""
        cursor = MockCursor(rows)
        
        result = cursor.fetchmany(0)
        
        # Should return empty list
        assert result == []
        
        # Should not consume any rows
        assert list(cursor._rows) == rows
    
    @given(st.lists(st.integers(), min_size=1))
    def test_fetch_order_preservation(self, rows):
        """Property: All fetch methods preserve row order"""
        # Test fetchone preserves order
        cursor1 = MockCursor(rows)
        fetched = []
        while True:
            row = cursor1.fetchone()
            if row is None:
                break
            fetched.append(row)
        assert fetched == rows
        
        # Test fetchall preserves order
        cursor2 = MockCursor(rows)
        assert cursor2.fetchall() == rows
        
        # Test fetchmany preserves order
        cursor3 = MockCursor(rows)
        fetched = []
        while True:
            batch = cursor3.fetchmany(2)
            if not batch:
                break
            fetched.extend(batch)
        assert fetched == rows
    
    @given(st.lists(st.integers(), min_size=10))
    def test_mixed_fetch_consistency(self, rows):
        """Property: Mixed fetch operations should be consistent"""
        cursor = MockCursor(rows)
        
        # Fetch one
        first = cursor.fetchone()
        assert first == rows[0]
        
        # Fetch many
        next_two = cursor.fetchmany(2)
        assert next_two == rows[1:3]
        
        # Fetch all remaining
        rest = cursor.fetchall()
        assert rest == rows[3:]
        
        # Everything should be consumed
        assert cursor.fetchone() is None
        assert cursor.fetchmany(10) == []
        assert cursor.fetchall() == []
    
    @given(st.lists(st.integers()), st.integers(min_value=1, max_value=100))
    def test_fetchmany_exceeding_available(self, rows, size):
        """Property: fetchmany(n) where n > len(rows) returns all rows"""
        cursor = MockCursor(rows)
        
        # Request more than available
        large_size = len(rows) + size
        result = cursor.fetchmany(large_size)
        
        # Should return all available rows
        assert result == rows
        
        # Should be empty now
        assert len(cursor._rows) == 0
        assert cursor.fetchmany(1) == []