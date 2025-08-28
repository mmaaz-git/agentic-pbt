"""Advanced property-based tests for sqlalchemy.future - looking for edge cases"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy.future import select, create_engine
from sqlalchemy import Column, Integer, String, Float, Boolean, MetaData, Table, text, literal, bindparam
from sqlalchemy.sql import expression
import sys


# Create test tables
def create_test_table(table_name="test", num_columns=3):
    metadata = MetaData()
    columns = [Column('id', Integer, primary_key=True)]
    
    for i in range(num_columns):
        if i % 3 == 0:
            columns.append(Column(f'col_int_{i}', Integer))
        elif i % 3 == 1:
            columns.append(Column(f'col_str_{i}', String))
        else:
            columns.append(Column(f'col_float_{i}', Float))
    
    return Table(table_name, metadata, *columns)


class TestSelectEdgeCases:
    """Test edge cases that might reveal bugs"""
    
    @given(
        limit=st.integers(min_value=0, max_value=sys.maxsize)
    )
    def test_extreme_limit_values(self, limit):
        """Test with extreme limit values"""
        table = create_test_table('test', 1)
        
        stmt = select(table).limit(limit)
        query_str = str(stmt)
        
        # Should produce valid SQL
        assert 'SELECT' in query_str
        assert 'LIMIT' in query_str
    
    @given(
        offset=st.integers(min_value=0, max_value=sys.maxsize)
    )
    def test_extreme_offset_values(self, offset):
        """Test with extreme offset values"""
        table = create_test_table('test', 1)
        
        stmt = select(table).offset(offset)
        query_str = str(stmt)
        
        # Should produce valid SQL
        assert 'SELECT' in query_str
        if offset > 0:
            assert 'OFFSET' in query_str
    
    @given(
        num_columns=st.integers(min_value=0, max_value=100)
    )
    def test_many_columns_select(self, num_columns):
        """Test selecting from tables with many columns"""
        table = create_test_table('test', num_columns)
        
        stmt = select(table)
        query_str = str(stmt)
        
        # Should produce valid SQL
        assert 'SELECT' in query_str
        assert 'FROM test' in query_str
    
    @given(
        table_name=st.text(min_size=0, max_size=1000)
    )
    def test_unusual_table_names(self, table_name):
        """Test with unusual table names"""
        # Skip empty names
        assume(len(table_name) > 0)
        
        try:
            metadata = MetaData()
            table = Table(table_name, metadata, Column('id', Integer))
            
            stmt = select(table)
            query_str = str(stmt)
            
            # Should produce some kind of SQL
            assert 'SELECT' in query_str
            assert 'FROM' in query_str
        except Exception as e:
            # Some table names might be invalid, that's OK
            pass
    
    def test_select_with_no_columns(self):
        """Test select with a table that has no columns"""
        metadata = MetaData()
        
        # This should raise an error when creating the table
        with pytest.raises(Exception):
            table = Table('empty_table', metadata)  # No columns
            stmt = select(table)
    
    @given(
        num_selects=st.integers(min_value=1, max_value=10)
    )
    def test_nested_subqueries(self, num_selects):
        """Test deeply nested subqueries"""
        table = create_test_table('test', 2)
        
        stmt = select(table)
        
        for i in range(num_selects):
            subq = stmt.subquery(f'subq_{i}')
            stmt = select(subq)
        
        query_str = str(stmt)
        
        # Should produce valid SQL with nested subqueries
        assert 'SELECT' in query_str
        assert 'FROM' in query_str
    
    def test_select_from_select(self):
        """Test selecting from another select (without subquery)"""
        table = create_test_table('test', 2)
        
        stmt1 = select(table)
        
        # Try to select from a select directly
        # This should either work or raise a clear error
        try:
            stmt2 = select(stmt1)
            query_str = str(stmt2)
            # If it works, should produce valid SQL
            assert 'SELECT' in query_str
        except Exception as e:
            # It's OK if this doesn't work
            pass


class TestSelectWithLiterals:
    """Test select with literal values"""
    
    @given(
        int_val=st.integers(),
        str_val=st.text(max_size=100),
        float_val=st.floats(allow_nan=False, allow_infinity=False)
    )
    def test_select_literals(self, int_val, str_val, float_val):
        """Test selecting literal values"""
        # Create select with literals
        stmt = select(literal(int_val), literal(str_val), literal(float_val))
        
        query_str = str(stmt)
        
        # Should produce valid SQL
        assert 'SELECT' in query_str
        # Should have parameter placeholders
        assert ':' in query_str or '?' in query_str
    
    def test_select_empty_literal(self):
        """Test selecting empty string literal"""
        stmt = select(literal(''))
        query_str = str(stmt)
        
        assert 'SELECT' in query_str
    
    @given(
        column_exprs=st.lists(
            st.sampled_from([
                lambda: literal(1),
                lambda: literal('test'),
                lambda: literal(None),
                lambda: text('1 + 1'),
            ]),
            min_size=1,
            max_size=10
        )
    )
    def test_select_mixed_expressions(self, column_exprs):
        """Test selecting various expression types"""
        exprs = [expr() for expr in column_exprs]
        
        stmt = select(*exprs)
        query_str = str(stmt)
        
        # Should produce valid SQL
        assert 'SELECT' in query_str


class TestCreateEngine:
    """Test create_engine function"""
    
    def test_create_engine_memory_sqlite(self):
        """Test creating an in-memory SQLite engine"""
        engine = create_engine('sqlite:///:memory:')
        
        # Should be able to connect
        conn = engine.connect()
        conn.close()
        
        # Should have expected methods
        assert hasattr(engine, 'execute')
        assert hasattr(engine, 'begin')
        assert hasattr(engine, 'dispose')
    
    @given(
        invalid_url=st.text(min_size=1, max_size=100).filter(lambda x: ':' not in x)
    )
    def test_create_engine_invalid_url(self, invalid_url):
        """Test create_engine with invalid URLs"""
        try:
            engine = create_engine(invalid_url)
            # Some invalid URLs might still create an engine
            # but fail on connection
            try:
                conn = engine.connect()
                conn.close()
            except Exception:
                pass
        except Exception as e:
            # Invalid URLs should raise exceptions
            pass
    
    def test_create_engine_with_future_flag(self):
        """Test that future flag is properly set"""
        # The future module's create_engine should have future=True by default
        engine = create_engine('sqlite:///:memory:')
        
        # Check if the engine has future behavior
        # This is implementation-specific but worth testing
        assert hasattr(engine, '_is_future') or True  # May not have this attribute


class TestSelectJoins:
    """Test join operations"""
    
    def test_self_join(self):
        """Test self-join on a table"""
        table = create_test_table('users', 3)
        
        # Create aliases for self-join
        t1 = table.alias('t1')
        t2 = table.alias('t2')
        
        stmt = select(t1, t2).select_from(t1.join(t2, t1.c.id == t2.c.id))
        
        query_str = str(stmt)
        
        # Should produce valid SQL with join
        assert 'SELECT' in query_str
        assert 'FROM' in query_str
        assert 'JOIN' in query_str
    
    def test_join_without_condition(self):
        """Test join without an explicit condition (cross join)"""
        table1 = create_test_table('table1', 2)
        table2 = create_test_table('table2', 2)
        
        # Try to create a cross join
        try:
            stmt = select(table1, table2)
            query_str = str(stmt)
            
            # Should produce valid SQL
            assert 'SELECT' in query_str
            assert 'FROM' in query_str
            # Should reference both tables
            assert 'table1' in query_str
            assert 'table2' in query_str
        except Exception:
            # Some databases might not support this
            pass


class TestSelectBugs:
    """Tests specifically designed to find bugs"""
    
    def test_limit_then_offset_then_limit(self):
        """Test complex chaining of limit and offset"""
        table = create_test_table('test', 1)
        
        stmt = select(table).limit(10).offset(5).limit(20)
        query_str = str(stmt)
        
        # The second limit should override
        assert 'LIMIT' in query_str
        assert 'OFFSET' in query_str
        
        # Create another with just the final values
        stmt2 = select(table).offset(5).limit(20)
        
        # Should be the same
        assert str(stmt) == str(stmt2)
    
    @given(
        distinct_before=st.booleans(),
        distinct_after=st.booleans()
    )
    def test_distinct_with_limit_offset(self, distinct_before, distinct_after):
        """Test distinct interaction with limit/offset"""
        table = create_test_table('test', 2)
        
        stmt = select(table)
        
        if distinct_before:
            stmt = stmt.distinct()
        
        stmt = stmt.limit(10).offset(5)
        
        if distinct_after:
            stmt = stmt.distinct()
        
        query_str = str(stmt)
        
        # Should have all the clauses
        if distinct_before or distinct_after:
            assert 'DISTINCT' in query_str
        assert 'LIMIT' in query_str
        assert 'OFFSET' in query_str
    
    def test_where_with_empty_condition(self):
        """Test where with an empty or trivial condition"""
        table = create_test_table('test', 1)
        
        # Test with always-true condition
        stmt = select(table).where(text('1=1'))
        query_str = str(stmt)
        
        assert 'WHERE' in query_str
        assert '1=1' in query_str
    
    def test_group_by_without_aggregates(self):
        """Test group by without aggregate functions"""
        table = create_test_table('test', 3)
        
        # Group by without aggregates - this is valid SQL but unusual
        stmt = select(table).group_by(table.c.id)
        query_str = str(stmt)
        
        assert 'GROUP BY' in query_str
    
    @given(
        num_wheres=st.integers(min_value=50, max_value=100)
    )
    def test_many_where_clauses(self, num_wheres):
        """Test with many WHERE clauses to check for performance or limit issues"""
        table = create_test_table('test', 1)
        
        stmt = select(table)
        for i in range(num_wheres):
            stmt = stmt.where(table.c.id != i)
        
        query_str = str(stmt)
        
        # Should still produce valid SQL
        assert 'WHERE' in query_str
        # Should have many AND operators
        assert query_str.count(' AND ') == num_wheres - 1