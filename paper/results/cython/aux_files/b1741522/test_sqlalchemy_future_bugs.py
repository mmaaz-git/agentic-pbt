"""Focused tests to find potential bugs in sqlalchemy.future"""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Float, MetaData, Table, text, literal
from sqlalchemy.sql.expression import Select
import warnings


def create_test_table(name="test"):
    metadata = MetaData()
    return Table(name, metadata,
        Column('id', Integer, primary_key=True),
        Column('value', Integer),
        Column('name', String)
    )


class TestSelectMutability:
    """Test if Select objects are properly immutable"""
    
    def test_select_immutability(self):
        """Test that select operations return new objects"""
        table = create_test_table()
        
        original = select(table)
        modified = original.where(table.c.id > 0)
        
        # Should be different objects
        assert original is not modified
        
        # Original should not be modified
        assert 'WHERE' not in str(original)
        assert 'WHERE' in str(modified)
    
    def test_chained_operations_immutability(self):
        """Test immutability with chained operations"""
        table = create_test_table()
        
        stmt1 = select(table)
        stmt2 = stmt1.where(table.c.id > 0)
        stmt3 = stmt2.distinct()
        stmt4 = stmt3.limit(10)
        
        # All should be different objects
        assert len({id(stmt1), id(stmt2), id(stmt3), id(stmt4)}) == 4
        
        # Each should have only its own modifications
        s1_str = str(stmt1)
        s2_str = str(stmt2)
        s3_str = str(stmt3)
        s4_str = str(stmt4)
        
        assert 'WHERE' not in s1_str
        assert 'WHERE' in s2_str
        assert 'DISTINCT' not in s2_str
        assert 'DISTINCT' in s3_str
        assert 'LIMIT' not in s3_str
        assert 'LIMIT' in s4_str


class TestSelectCornerCases:
    """Test corner cases that might expose bugs"""
    
    @given(
        limit1=st.integers(min_value=0, max_value=1000),
        offset1=st.integers(min_value=0, max_value=1000),
        limit2=st.integers(min_value=0, max_value=1000),
        offset2=st.integers(min_value=0, max_value=1000)
    )
    def test_limit_offset_combinations(self, limit1, offset1, limit2, offset2):
        """Test various combinations of limit and offset"""
        table = create_test_table()
        
        # Apply limit and offset in different orders
        stmt1 = select(table).limit(limit1).offset(offset1).limit(limit2).offset(offset2)
        stmt2 = select(table).limit(limit2).offset(offset2)
        
        # The final values should win
        assert str(stmt1) == str(stmt2)
    
    def test_zero_limit(self):
        """Test limit(0) which should return no rows"""
        table = create_test_table()
        
        stmt = select(table).limit(0)
        query_str = str(stmt)
        
        assert 'LIMIT' in query_str
        # The limit value should be 0 (represented as a parameter)
        assert ':param_1' in query_str or '?' in query_str
    
    def test_distinct_distinct_false(self):
        """Test calling distinct() then distinct(False)"""
        table = create_test_table()
        
        # First add distinct, then try to remove it
        stmt1 = select(table).distinct()
        
        # Try to remove distinct (if supported)
        try:
            stmt2 = stmt1.distinct(False)
            
            # If it works, check that distinct was removed
            if 'DISTINCT' in str(stmt2):
                # distinct(False) didn't remove DISTINCT - potential bug?
                print(f"distinct(False) didn't remove DISTINCT: {str(stmt2)}")
        except TypeError:
            # distinct() might not accept arguments
            pass
    
    @given(
        num_wheres=st.integers(min_value=100, max_value=500)
    )
    @settings(max_examples=10, deadline=None)
    def test_extreme_where_chaining(self, num_wheres):
        """Test with extreme number of WHERE conditions"""
        table = create_test_table()
        
        stmt = select(table)
        for i in range(num_wheres):
            stmt = stmt.where(table.c.id != i)
        
        query_str = str(stmt)
        
        # Should still work
        assert 'WHERE' in query_str
        # Should have the right number of AND operators
        and_count = query_str.count(' AND ')
        assert and_count == num_wheres - 1
    
    def test_select_from_literal_only(self):
        """Test select with only literals, no table"""
        # This is valid SQL: SELECT 1, 'hello', 3.14
        stmt = select(literal(1), literal('hello'), literal(3.14))
        
        query_str = str(stmt)
        
        # Should not have FROM clause
        assert 'SELECT' in query_str
        assert 'FROM' not in query_str
    
    @given(
        text_expr=st.text(min_size=1, max_size=100)
    )
    def test_select_text_expression(self, text_expr):
        """Test select with arbitrary text expressions"""
        # Skip potentially dangerous SQL
        assume('DROP' not in text_expr.upper())
        assume('DELETE' not in text_expr.upper())
        assume(';' not in text_expr)
        
        try:
            stmt = select(text(text_expr))
            query_str = str(stmt)
            
            # Should include the text expression
            assert 'SELECT' in query_str
            assert text_expr in query_str
        except Exception:
            # Some text might not be valid SQL expressions
            pass


class TestSelectAliasing:
    """Test aliasing and labeling behavior"""
    
    def test_column_label_collision(self):
        """Test when column labels might collide"""
        metadata = MetaData()
        
        # Create two tables with same column names
        table1 = Table('users', metadata,
            Column('id', Integer),
            Column('name', String)
        )
        
        table2 = Table('accounts', metadata,
            Column('id', Integer),
            Column('name', String)
        )
        
        # Select from both without aliasing
        stmt = select(table1.c.id, table1.c.name, table2.c.id, table2.c.name).select_from(
            table1.join(table2, table1.c.id == table2.c.id)
        )
        
        query_str = str(stmt)
        
        # Should handle column name collisions properly
        assert 'users.id' in query_str
        assert 'accounts.id' in query_str
    
    def test_self_join_aliasing(self):
        """Test self-join with proper aliasing"""
        table = create_test_table('users')
        
        u1 = table.alias('u1')
        u2 = table.alias('u2')
        
        # Self join
        stmt = select(u1.c.id, u2.c.id).select_from(
            u1.join(u2, u1.c.id < u2.c.id)
        )
        
        query_str = str(stmt)
        
        # Should have both aliases
        assert 'u1' in query_str
        assert 'u2' in query_str
        assert 'JOIN' in query_str


class TestSelectParameterBinding:
    """Test parameter binding edge cases"""
    
    @given(
        values=st.lists(
            st.integers(min_value=-1000, max_value=1000),
            min_size=1,
            max_size=20
        )
    )
    def test_many_parameters(self, values):
        """Test with many bound parameters"""
        table = create_test_table()
        
        stmt = select(table)
        
        # Add many WHERE conditions with parameters
        for val in values:
            stmt = stmt.where(table.c.value != val)
        
        query_str = str(stmt)
        
        # Should have parameter placeholders
        param_count = query_str.count(':value_') or query_str.count('?')
        assert param_count >= len(values)
    
    def test_same_value_multiple_conditions(self):
        """Test using the same value in multiple conditions"""
        table = create_test_table()
        
        # Use the same value multiple times
        stmt = select(table).where(
            table.c.id > 5
        ).where(
            table.c.value < 5
        ).where(
            table.c.id != 5
        )
        
        query_str = str(stmt)
        
        # Should handle the repeated value correctly
        assert 'WHERE' in query_str
        assert query_str.count('AND') == 2


class TestSelectGroupByHaving:
    """Test GROUP BY and HAVING interactions"""
    
    def test_having_without_group_by(self):
        """Test HAVING without GROUP BY (usually invalid SQL)"""
        table = create_test_table()
        
        # Try to use HAVING without GROUP BY
        stmt = select(table).having(table.c.id > 0)
        
        query_str = str(stmt)
        
        # SQLAlchemy might allow this even though it's invalid SQL
        # This could be a bug if it doesn't validate
        assert 'HAVING' in query_str
        # Note: This would fail at execution time on most databases
    
    def test_group_by_after_having(self):
        """Test adding GROUP BY after HAVING"""
        table = create_test_table()
        
        # Add HAVING first, then GROUP BY
        stmt = select(table).having(table.c.id > 0).group_by(table.c.id)
        
        query_str = str(stmt)
        
        # Both should be present
        assert 'GROUP BY' in query_str
        assert 'HAVING' in query_str
        
        # GROUP BY should come before HAVING in the SQL
        group_pos = query_str.find('GROUP BY')
        having_pos = query_str.find('HAVING')
        assert group_pos < having_pos


class TestSelectNullHandling:
    """Test NULL value handling"""
    
    def test_null_in_where(self):
        """Test NULL comparisons in WHERE clause"""
        table = create_test_table()
        
        # Test various NULL comparisons
        stmt1 = select(table).where(table.c.name == None)
        stmt2 = select(table).where(table.c.name != None)
        stmt3 = select(table).where(table.c.name.is_(None))
        stmt4 = select(table).where(table.c.name.isnot(None))
        
        # Should use IS NULL / IS NOT NULL
        assert 'IS NULL' in str(stmt1)
        assert 'IS NOT NULL' in str(stmt2)
        assert 'IS NULL' in str(stmt3)
        assert 'IS NOT NULL' in str(stmt4)
    
    def test_null_literal_select(self):
        """Test selecting NULL literal"""
        stmt = select(literal(None))
        
        query_str = str(stmt)
        
        # Should handle NULL literal
        assert 'SELECT' in query_str
        # Should have NULL or a parameter
        assert 'NULL' in query_str.upper() or ':' in query_str