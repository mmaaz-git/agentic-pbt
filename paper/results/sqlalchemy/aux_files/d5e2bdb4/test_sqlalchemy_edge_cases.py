"""Additional edge case tests for sqlalchemy.sql to find potential bugs."""

import sqlalchemy.sql as sql
from sqlalchemy import column, table, literal, true, false
from hypothesis import given, strategies as st, assume, settings
import pytest
import sys


class TestUnicodeAndSpecialCharacters:
    """Test handling of Unicode and special characters."""
    
    @given(st.text(min_size=1, max_size=50))
    def test_column_name_with_unicode(self, name):
        """Test columns with Unicode names."""
        assume(name.strip() and name.isidentifier())
        try:
            t = table('test', column(name))
            expr = getattr(t.c, name) == 1
            result = sql.and_(expr, sql.true())
            result_str = str(result)
            assert isinstance(result_str, str)
            # Column name should appear in result
            assert name in result_str or f'"{name}"' in result_str
        except (AttributeError, KeyError):
            # Some names might not be valid identifiers
            pass
    
    @given(st.text())
    def test_literal_with_special_chars(self, text):
        """Test literal values with special characters."""
        lit = sql.literal(text)
        assert lit.value == text
        # Should be able to use in expressions
        t = table('t', column('x'))
        expr = t.c.x == lit
        assert str(expr)  # Should not crash


class TestNumericEdgeCases:
    """Test numeric edge cases."""
    
    @given(st.one_of(
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(float('nan'))
    ))
    def test_literal_special_floats(self, value):
        """Test literal with special float values."""
        lit = sql.literal(value)
        if value != value:  # NaN check
            assert lit.value != lit.value  # NaN != NaN
        else:
            assert lit.value == value
    
    @given(st.integers())
    def test_between_with_large_numbers(self, x):
        """Test between with very large numbers."""
        t = table('t', column('value'))
        # Test with max integers
        expr1 = sql.between(t.c.value, x, sys.maxsize)
        expr2 = sql.between(t.c.value, -sys.maxsize, x)
        assert 'BETWEEN' in str(expr1)
        assert 'BETWEEN' in str(expr2)


class TestRecursiveStructures:
    """Test deeply nested and recursive structures."""
    
    @given(st.integers(min_value=1, max_value=100))
    def test_deeply_nested_and(self, depth):
        """Test deeply nested and_ expressions."""
        t = table('t', column('x'))
        expr = t.c.x == 1
        
        # Build deeply nested expression
        result = expr
        for _ in range(depth):
            result = sql.and_(result, sql.true())
        
        result_str = str(result)
        assert isinstance(result_str, str)
        # Should still produce valid SQL
        assert 't.x' in result_str
    
    @given(st.integers(min_value=1, max_value=50))
    def test_alternating_not(self, count):
        """Test alternating not_ operators."""
        t = table('t', column('x'))
        expr = t.c.x == 1
        
        result = expr
        for i in range(count):
            result = sql.not_(result)
        
        result_str = str(result)
        # Even number of nots should return to original
        if count % 2 == 0:
            assert result_str == str(expr)
        else:
            assert result_str == str(sql.not_(expr))


class TestEmptyAndNullHandling:
    """Test empty and null value handling."""
    
    def test_and_with_empty_list(self):
        """Test and_() with empty args (deprecated but should handle)."""
        # This is deprecated but should not crash
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = sql.and_()
            # Should produce empty or true-like result
            assert str(result) == '' or str(result) == 'true'
    
    def test_or_with_empty_list(self):
        """Test or_() with empty args (deprecated but should handle)."""
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = sql.or_()
            # Should produce empty or false-like result
            assert str(result) == '' or str(result) == 'false'
    
    @given(st.lists(st.none(), min_size=1, max_size=10))
    def test_and_all_none(self, none_list):
        """Test and_ with all None values."""
        result = sql.and_(*none_list)
        result_str = str(result)
        # All Nones should result in NULL or similar
        assert 'NULL' in result_str


class TestMixedOperations:
    """Test mixing different operations."""
    
    @given(st.booleans(), st.booleans(), st.booleans())
    def test_mixed_logical_ops(self, a, b, c):
        """Test mixing and_, or_, not_ with Python booleans."""
        # Complex expression: (a AND b) OR (NOT c)
        result = sql.or_(sql.and_(a, b), sql.not_(c))
        result_str = str(result)
        
        # Verify logical evaluation matches Python
        python_result = (a and b) or (not c)
        
        if python_result:
            # If Python evaluates to True, SQL should be 'true' or contain true
            assert result_str == 'true' or 'true' in result_str.lower()
        else:
            # If Python evaluates to False, SQL should be 'false'
            assert result_str == 'false'
    
    @given(st.integers(min_value=-100, max_value=100),
           st.integers(min_value=-100, max_value=100),
           st.integers(min_value=-100, max_value=100))
    def test_nested_between(self, x, y, z):
        """Test between in logical expressions."""
        t = table('t', column('a'), column('b'))
        
        # Create complex expression with between
        between1 = sql.between(t.c.a, x, y)
        between2 = sql.between(t.c.b, y, z)
        
        # Combine with logical operators
        combined = sql.and_(between1, sql.not_(between2))
        result_str = str(combined)
        
        # Should have both BETWEEN clauses
        assert result_str.count('BETWEEN') >= 1
        assert 'NOT' in result_str or '!=' in result_str


class TestStringRepresentation:
    """Test string representation consistency."""
    
    @given(st.lists(st.booleans(), min_size=2, max_size=5))
    def test_and_associativity_string(self, bool_list):
        """Test if and_ string representation is consistent."""
        # Build expression left-to-right
        left_result = bool_list[0]
        for b in bool_list[1:]:
            left_result = sql.and_(left_result, b)
        
        # Build expression all at once
        flat_result = sql.and_(*bool_list)
        
        # String representations should be equivalent
        left_str = str(left_result)
        flat_str = str(flat_result)
        
        # Both should evaluate to same logical result
        python_result = all(bool_list)
        
        if python_result:
            assert left_str == 'true' and flat_str == 'true'
        elif not any(bool_list):
            assert left_str == 'false' and flat_str == 'false'


class TestLiteralTypePreservation:
    """Test that literal values preserve their types correctly."""
    
    @given(st.integers(min_value=0, max_value=255))
    def test_literal_byte_values(self, value):
        """Test literal with byte-sized values."""
        lit = sql.literal(value)
        assert lit.value == value
        assert type(lit.value) == int
    
    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    def test_literal_probability_values(self, value):
        """Test literal with probability values [0, 1]."""
        lit = sql.literal(value)
        assert lit.value == value
        assert isinstance(lit.value, float)
    
    @given(st.one_of(
        st.just(0),
        st.just(1),
        st.just(-1),
        st.just(sys.maxsize),
        st.just(-sys.maxsize - 1)
    ))
    def test_literal_boundary_integers(self, value):
        """Test literal with boundary integer values."""
        lit = sql.literal(value)
        assert lit.value == value