"""Property-based tests for sqlalchemy.future module"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Float, Boolean, MetaData, Table, and_, or_, text


# Create test tables for our tests
def create_test_table(table_name="test_table", num_columns=3):
    """Create a test table with various column types"""
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


# Strategy for generating table names
table_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L',), min_codepoint=97, max_codepoint=122),
    min_size=1,
    max_size=30
).filter(lambda x: not x.startswith('_'))


# Strategy for generating column counts
column_count_strategy = st.integers(min_value=1, max_value=10)


class TestSelectIdempotence:
    """Test idempotence properties of Select methods"""
    
    @given(table_name=table_name_strategy, num_cols=column_count_strategy)
    def test_distinct_idempotence(self, table_name, num_cols):
        """Calling distinct() multiple times should be idempotent"""
        table = create_test_table(table_name, num_cols)
        
        stmt1 = select(table).distinct()
        stmt2 = select(table).distinct().distinct()
        stmt3 = select(table).distinct().distinct().distinct()
        
        # Convert to string for comparison
        assert str(stmt1) == str(stmt2)
        assert str(stmt2) == str(stmt3)
    
    @given(
        table_name=table_name_strategy,
        num_cols=column_count_strategy,
        limit1=st.integers(min_value=0, max_value=1000),
        limit2=st.integers(min_value=0, max_value=1000)
    )
    def test_limit_override(self, table_name, num_cols, limit1, limit2):
        """Setting limit multiple times should use the last limit"""
        table = create_test_table(table_name, num_cols)
        
        stmt1 = select(table).limit(limit1)
        stmt2 = select(table).limit(limit1).limit(limit2)
        stmt3 = select(table).limit(limit2)
        
        # The second limit should override the first
        # Both should produce the same query
        assert str(stmt2) == str(stmt3)
    
    @given(
        table_name=table_name_strategy,
        num_cols=column_count_strategy,
        offset1=st.integers(min_value=0, max_value=1000),
        offset2=st.integers(min_value=0, max_value=1000)
    )
    def test_offset_override(self, table_name, num_cols, offset1, offset2):
        """Setting offset multiple times should use the last offset"""
        table = create_test_table(table_name, num_cols)
        
        stmt1 = select(table).offset(offset1)
        stmt2 = select(table).offset(offset1).offset(offset2)
        stmt3 = select(table).offset(offset2)
        
        # The second offset should override the first
        assert str(stmt2) == str(stmt3)


class TestSelectEquivalence:
    """Test equivalence between different Select methods"""
    
    @given(table_name=table_name_strategy, num_cols=column_count_strategy)
    def test_filter_where_equivalence(self, table_name, num_cols):
        """filter() and where() should be equivalent"""
        table = create_test_table(table_name, num_cols)
        
        # Test with a simple condition
        condition = table.c.id > 0
        
        stmt_where = select(table).where(condition)
        stmt_filter = select(table).filter(condition)
        
        assert str(stmt_where) == str(stmt_filter)
    
    @given(
        table_name=table_name_strategy,
        num_cols=column_count_strategy,
        values=st.lists(st.integers(min_value=-100, max_value=100), min_size=2, max_size=5)
    )
    def test_multiple_where_vs_and(self, table_name, num_cols, values):
        """Multiple where() calls should be equivalent to using and_()"""
        table = create_test_table(table_name, num_cols)
        
        # Create multiple conditions
        conditions = [table.c.id > val for val in values]
        
        # Chain multiple where calls
        stmt_chained = select(table)
        for cond in conditions:
            stmt_chained = stmt_chained.where(cond)
        
        # Use and_() to combine conditions
        stmt_and = select(table).where(and_(*conditions))
        
        # They should produce the same query
        assert str(stmt_chained) == str(stmt_and)


class TestSelectChaining:
    """Test method chaining properties"""
    
    @given(
        table_name=table_name_strategy,
        num_cols=column_count_strategy,
        num_wheres=st.integers(min_value=1, max_value=5)
    )
    def test_where_accumulation(self, table_name, num_cols, num_wheres):
        """Multiple where() calls should accumulate conditions"""
        table = create_test_table(table_name, num_cols)
        
        stmt = select(table)
        conditions = []
        
        for i in range(num_wheres):
            condition = table.c.id > i
            conditions.append(condition)
            stmt = stmt.where(condition)
        
        # The resulting query should contain all conditions
        query_str = str(stmt)
        
        # Each condition should appear in the WHERE clause
        assert 'WHERE' in query_str
        # Count the number of AND operators (should be num_wheres - 1)
        if num_wheres > 1:
            assert query_str.count(' AND ') == num_wheres - 1
    
    @given(
        table_name=table_name_strategy,
        num_cols=column_count_strategy,
        num_havings=st.integers(min_value=1, max_value=5)
    )
    def test_having_accumulation(self, table_name, num_cols, num_havings):
        """Multiple having() calls should accumulate conditions"""
        table = create_test_table(table_name, num_cols)
        
        # Need group_by for having to make sense
        stmt = select(table).group_by(table.c.id)
        
        for i in range(num_havings):
            condition = table.c.id > i
            stmt = stmt.having(condition)
        
        query_str = str(stmt)
        
        # Should have HAVING clause
        assert 'HAVING' in query_str
        # Count the number of AND operators in HAVING
        if num_havings > 1:
            having_part = query_str.split('HAVING')[1] if 'HAVING' in query_str else ''
            assert having_part.count(' AND ') == num_havings - 1


class TestSelectBoundaries:
    """Test boundary conditions and edge cases"""
    
    @given(table_name=table_name_strategy)
    def test_empty_select(self, table_name):
        """select() with just a table should work"""
        table = create_test_table(table_name, 1)
        stmt = select(table)
        
        # Should produce a valid query
        query_str = str(stmt)
        assert 'SELECT' in query_str
        assert 'FROM' in query_str
        assert table_name in query_str
    
    @given(limit=st.integers(min_value=-100, max_value=-1))
    def test_negative_limit(self, limit):
        """Negative limits should either be rejected or handled properly"""
        table = create_test_table('test', 1)
        
        # This might raise an error or handle it somehow
        try:
            stmt = select(table).limit(limit)
            # If it doesn't raise, check the query
            query_str = str(stmt)
            # The limit should be in the query
            assert 'LIMIT' in query_str
        except (ValueError, TypeError) as e:
            # It's OK to reject negative limits
            pass
    
    @given(offset=st.integers(min_value=-100, max_value=-1))
    def test_negative_offset(self, offset):
        """Negative offsets should either be rejected or handled properly"""
        table = create_test_table('test', 1)
        
        try:
            stmt = select(table).offset(offset)
            query_str = str(stmt)
            # The offset should be in the query
            assert 'OFFSET' in query_str
        except (ValueError, TypeError) as e:
            # It's OK to reject negative offsets
            pass
    
    @given(
        table_name=table_name_strategy,
        distinct_calls=st.integers(min_value=0, max_value=10)
    )
    def test_many_distinct_calls(self, table_name, distinct_calls):
        """Many distinct() calls should still be idempotent"""
        table = create_test_table(table_name, 1)
        
        stmt = select(table)
        for _ in range(distinct_calls):
            stmt = stmt.distinct()
        
        # Should be the same as calling distinct once (or not at all if 0)
        if distinct_calls > 0:
            expected = select(table).distinct()
            assert str(stmt) == str(expected)
        else:
            expected = select(table)
            assert str(stmt) == str(expected)


class TestSelectComplexProperties:
    """Test more complex properties involving multiple operations"""
    
    @given(
        table_name=table_name_strategy,
        operations=st.lists(
            st.sampled_from(['distinct', 'where', 'limit', 'offset']),
            min_size=1,
            max_size=10
        )
    )
    def test_operation_chaining_produces_valid_sql(self, table_name, operations):
        """Chaining various operations should always produce valid SQL"""
        table = create_test_table(table_name, 3)
        stmt = select(table)
        
        for op in operations:
            if op == 'distinct':
                stmt = stmt.distinct()
            elif op == 'where':
                stmt = stmt.where(table.c.id > 0)
            elif op == 'limit':
                stmt = stmt.limit(10)
            elif op == 'offset':
                stmt = stmt.offset(5)
        
        # Should produce a valid query string
        query_str = str(stmt)
        assert 'SELECT' in query_str
        assert 'FROM' in query_str
        assert table_name in query_str
    
    @given(
        table_name=table_name_strategy,
        num_cols=column_count_strategy
    )
    def test_subquery_creation(self, table_name, num_cols):
        """Creating a subquery should preserve the query structure"""
        table = create_test_table(table_name, num_cols)
        
        # Create a select with some operations
        stmt = select(table).where(table.c.id > 0).distinct().limit(10)
        
        # Create a subquery
        subq = stmt.subquery()
        
        # The subquery should have a name
        assert hasattr(subq, 'name')
        
        # We should be able to select from the subquery
        stmt2 = select(subq)
        query_str = str(stmt2)
        
        # Should contain SELECT and FROM
        assert 'SELECT' in query_str
        assert 'FROM' in query_str


class TestSelectWithNoneValues:
    """Test handling of None values in various contexts"""
    
    @given(table_name=table_name_strategy)
    def test_limit_none(self, table_name):
        """limit(None) should remove the limit"""
        table = create_test_table(table_name, 1)
        
        stmt1 = select(table).limit(10).limit(None)
        stmt2 = select(table)
        
        # Should be equivalent to no limit
        assert str(stmt1) == str(stmt2)
    
    @given(table_name=table_name_strategy)
    def test_offset_none(self, table_name):
        """offset(None) should remove the offset"""
        table = create_test_table(table_name, 1)
        
        stmt1 = select(table).offset(10).offset(None)
        stmt2 = select(table)
        
        # Should be equivalent to no offset
        assert str(stmt1) == str(stmt2)
    
    @given(table_name=table_name_strategy)
    def test_where_with_none_comparison(self, table_name):
        """Comparing with None should use IS NULL/IS NOT NULL"""
        table = create_test_table(table_name, 2)
        
        # Test != None
        stmt1 = select(table).where(table.c.col_str_1 != None)
        query_str1 = str(stmt1)
        assert 'IS NOT NULL' in query_str1
        
        # Test == None
        stmt2 = select(table).where(table.c.col_str_1 == None)
        query_str2 = str(stmt2)
        assert 'IS NULL' in query_str2