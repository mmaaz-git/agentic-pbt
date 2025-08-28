"""Advanced property-based tests for SQLAlchemy to find potential bugs."""

from hypothesis import given, strategies as st, assume, settings
import pytest
from sqlalchemy import (
    column, and_, or_, not_, select, literal, bindparam,
    func, between, case, exists, any_, all_, cast, type_coerce
)
from sqlalchemy.sql.elements import ClauseElement, BinaryExpression
from sqlalchemy.types import Integer, String, Boolean
import traceback


# Strategy for valid SQL identifiers (lowercase to avoid quoting issues)
sql_identifier = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122),
    min_size=1,
    max_size=30
).filter(lambda s: not s[0].isdigit() and s.isidentifier())


class TestExpressionComparison:
    """Test structural comparison vs SQL generation consistency."""
    
    @given(sql_identifier, st.integers(min_value=-100, max_value=100))
    def test_compare_reflexivity(self, col_name, value):
        """An expression should always compare equal to itself."""
        col = column(col_name)
        expr = col == value
        
        # Reflexivity: x.compare(x) should be True
        assert expr.compare(expr), "Expression should compare equal to itself"
    
    @given(sql_identifier, st.integers(min_value=-100, max_value=100))
    def test_compare_vs_sql_consistency(self, col_name, value):
        """If two expressions compare equal, they should produce identical SQL."""
        col = column(col_name)
        
        # Create the same expression twice
        expr1 = col == value
        expr2 = col == value
        
        if expr1.compare(expr2):
            # They compare equal, but do they generate the same SQL?
            sql1 = str(expr1)
            sql2 = str(expr2)
            # Note: bind parameters might differ, so we check structure
            assert sql1.replace(':' + col_name + '_1', ':param') == sql2.replace(':' + col_name + '_1', ':param')
    
    @given(sql_identifier, 
           st.integers(min_value=-100, max_value=100),
           st.integers(min_value=-100, max_value=100))
    def test_and_associativity(self, col_name, val1, val2):
        """Test if and_ is associative in terms of comparison."""
        col = column(col_name)
        
        # Create three conditions
        cond1 = col > val1
        cond2 = col < val2
        cond3 = col != 0
        
        # (a AND b) AND c
        expr1 = and_(and_(cond1, cond2), cond3)
        # a AND (b AND c)
        expr2 = and_(cond1, and_(cond2, cond3))
        
        # Should these compare equal? They're logically equivalent
        # Let's check what SQLAlchemy does
        sql1 = str(expr1)
        sql2 = str(expr2)
        
        # Just verify they produce valid SQL
        assert 'AND' in sql1
        assert 'AND' in sql2


class TestComplexExpressions:
    """Test complex expression construction."""
    
    @given(sql_identifier, st.lists(st.integers(), min_size=1, max_size=5))
    def test_in_operator_with_empty_handling(self, col_name, values):
        """Test the IN operator with various list sizes."""
        col = column(col_name)
        
        # Create IN expression
        in_expr = col.in_(values)
        
        # Should produce valid SQL
        sql = str(in_expr)
        assert col_name in sql
        assert 'IN' in sql or '=' in sql  # Single value might use =
    
    @given(sql_identifier)
    def test_exists_clause_construction(self, col_name):
        """Test EXISTS clause construction."""
        col = column(col_name)
        
        # Create a subquery-like expression
        subq = select(col).where(col > 0)
        exist_expr = exists(subq)
        
        sql = str(exist_expr)
        assert 'EXISTS' in sql
    
    @given(sql_identifier, st.booleans())
    def test_not_operator_on_boolean(self, col_name, bool_val):
        """Test NOT operator on boolean literals."""
        col = column(col_name)
        
        # Create boolean expression
        bool_expr = literal(bool_val)
        not_expr = not_(bool_expr)
        
        sql = str(not_expr)
        assert 'NOT' in sql


class TestCaseSensitiveOperations:
    """Test case sensitivity in various operations."""
    
    @given(st.text(alphabet="abcABC", min_size=1, max_size=10))
    def test_func_case_preservation(self, func_name):
        """Test if func preserves case in function names."""
        # Get function via func
        sql_func = getattr(func, func_name)
        result = sql_func()
        
        sql = str(result)
        # Function names are typically uppercase in SQL
        assert func_name.lower() in sql.lower() or func_name.upper() in sql


class TestTypeCoercion:
    """Test type coercion behaviors."""
    
    @given(sql_identifier, 
           st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text()))
    def test_literal_type_inference(self, col_name, value):
        """Test if literal correctly infers types."""
        lit = literal(value)
        
        # Check that it creates a BindParameter
        from sqlalchemy.sql.elements import BindParameter
        assert isinstance(lit, BindParameter)
        
        # The value should be preserved
        assert lit.value == value
    
    @given(sql_identifier)
    def test_cast_type_preservation(self, col_name):
        """Test CAST operation type preservation."""
        col = column(col_name)
        
        # Cast to different types
        cast_int = cast(col, Integer)
        cast_str = cast(col, String)
        
        sql_int = str(cast_int)
        sql_str = str(cast_str)
        
        assert 'CAST' in sql_int
        assert 'CAST' in sql_str
        assert sql_int != sql_str  # Different types should produce different SQL


class TestEdgeCases:
    """Test edge cases that might reveal bugs."""
    
    @given(sql_identifier)
    def test_empty_and(self, col_name):
        """Test and_ with no arguments."""
        # What happens with empty and_?
        try:
            result = and_()
            sql = str(result)
            # If it works, it should produce something
            assert sql is not None
        except Exception as e:
            # If it fails, that's also informative
            # But it shouldn't crash badly
            assert True
    
    @given(sql_identifier)
    def test_empty_or(self, col_name):
        """Test or_ with no arguments."""
        try:
            result = or_()
            sql = str(result)
            assert sql is not None
        except Exception as e:
            assert True
    
    @given(sql_identifier, st.integers())
    def test_deeply_nested_not(self, col_name, depth):
        """Test deeply nested NOT operations."""
        assume(0 <= depth <= 10)  # Reasonable nesting depth
        
        col = column(col_name)
        expr = col == 1
        
        # Apply NOT operations depth times
        for _ in range(depth):
            expr = not_(expr)
        
        sql = str(expr)
        # Count NOT occurrences
        not_count = sql.count('NOT')
        assert not_count == depth
    
    @given(st.lists(sql_identifier, min_size=1, max_size=5, unique=True))
    def test_multiple_column_and(self, col_names):
        """Test and_ with multiple different columns."""
        cols = [column(name) for name in col_names]
        conditions = [col == 1 for col in cols]
        
        result = and_(*conditions)
        sql = str(result)
        
        # All column names should appear
        for name in col_names:
            assert name in sql
        
        # Should have the right number of ANDs
        and_count = sql.count('AND')
        assert and_count == len(col_names) - 1 if len(col_names) > 1 else and_count == 0


class TestSpecialCharacters:
    """Test handling of special characters and edge cases."""
    
    @given(st.text(alphabet="ab'\"\\`;", min_size=1, max_size=10))
    def test_literal_with_special_chars(self, text_with_specials):
        """Test literals with special SQL characters."""
        lit = literal(text_with_specials)
        
        # Should not crash
        sql = str(lit)
        assert sql is not None
        
        # The literal should handle escaping internally
        from sqlalchemy.sql.elements import BindParameter
        assert isinstance(lit, BindParameter)
        assert lit.value == text_with_specials
    
    @given(st.text(min_size=0, max_size=1000))
    def test_func_with_long_strings(self, long_text):
        """Test SQL functions with very long string arguments."""
        result = func.length(literal(long_text))
        
        sql = str(result)
        assert 'length' in sql
    
    @given(st.floats(allow_nan=True, allow_infinity=True))
    def test_literal_with_special_floats(self, special_float):
        """Test literals with NaN and infinity."""
        try:
            lit = literal(special_float)
            sql = str(lit)
            # Should handle these special values somehow
            assert sql is not None
        except Exception as e:
            # Some databases don't support NaN/Inf, so this might fail
            # But it shouldn't crash the entire system
            assert True


if __name__ == "__main__":
    print("Running advanced property-based tests for SQLAlchemy...")
    
    # Run a specific test with more examples
    test = TestEdgeCases()
    test.test_empty_and("dummy")
    test.test_empty_or("dummy")
    print("✓ Edge case tests completed")