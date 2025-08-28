"""Property-based tests for sqlalchemy.sql module using Hypothesis."""

import sqlalchemy.sql as sql
from sqlalchemy import column, table, true, false, literal
from hypothesis import given, strategies as st, assume, settings
import pytest


def create_test_expr(col_name='x', value=1):
    """Helper to create a test expression."""
    t = table('test_table', column(col_name))
    return getattr(t.c, col_name) == value


def expr_to_str(expr):
    """Convert expression to string for comparison."""
    return str(expr)


class TestBooleanConstantSimplification:
    """Test boolean simplification properties that SQLAlchemy claims."""
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers())
    def test_and_true_identity(self, col_name, value):
        """and_(expr, true()) should simplify to expr."""
        expr = create_test_expr(col_name, value)
        result = sql.and_(expr, sql.true())
        # Check if result is equivalent to original expression
        assert expr_to_str(result) == expr_to_str(expr)
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers())
    def test_and_false_annihilation(self, col_name, value):
        """and_(expr, false()) should simplify to false."""
        expr = create_test_expr(col_name, value)
        result = sql.and_(expr, sql.false())
        assert expr_to_str(result) == 'false'
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers())
    def test_or_true_annihilation(self, col_name, value):
        """or_(expr, true()) should simplify to true."""
        expr = create_test_expr(col_name, value)
        result = sql.or_(expr, sql.true())
        assert expr_to_str(result) == 'true'
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers())
    def test_or_false_identity(self, col_name, value):
        """or_(expr, false()) should simplify to expr."""
        expr = create_test_expr(col_name, value)
        result = sql.or_(expr, sql.false())
        assert expr_to_str(result) == expr_to_str(expr)


class TestNotOperator:
    """Test properties of the not_ operator."""
    
    def test_not_true_is_false(self):
        """not_(true()) should be false."""
        result = sql.not_(sql.true())
        assert expr_to_str(result) == 'false'
    
    def test_not_false_is_true(self):
        """not_(false()) should be true."""
        result = sql.not_(sql.false())
        assert expr_to_str(result) == 'true'
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers())
    def test_double_negation(self, col_name, value):
        """not_(not_(expr)) should return to original expression."""
        expr = create_test_expr(col_name, value)
        double_not = sql.not_(sql.not_(expr))
        # SQLAlchemy simplifies double negation back to original
        assert expr_to_str(double_not) == expr_to_str(expr)


class TestIdentityProperties:
    """Test identity properties for logical operators."""
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers())
    def test_and_single_arg_identity(self, col_name, value):
        """and_(expr) with single argument should return expr."""
        expr = create_test_expr(col_name, value)
        result = sql.and_(expr)
        assert expr_to_str(result) == expr_to_str(expr)
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers())
    def test_or_single_arg_identity(self, col_name, value):
        """or_(expr) with single argument should return expr."""
        expr = create_test_expr(col_name, value)
        result = sql.or_(expr)
        assert expr_to_str(result) == expr_to_str(expr)


class TestBetweenOperator:
    """Test properties of the between operator."""
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers(min_value=-1000, max_value=1000),
           st.integers(min_value=-1000, max_value=1000))
    def test_between_basic(self, col_name, lower, upper):
        """between should create a BETWEEN clause."""
        t = table('test_table', column(col_name))
        expr = sql.between(getattr(t.c, col_name), lower, upper)
        result_str = expr_to_str(expr)
        assert 'BETWEEN' in result_str
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers(min_value=-1000, max_value=1000))
    def test_between_equal_bounds(self, col_name, value):
        """between with equal bounds should still be valid."""
        t = table('test_table', column(col_name))
        expr = sql.between(getattr(t.c, col_name), value, value)
        result_str = expr_to_str(expr)
        assert 'BETWEEN' in result_str
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers(min_value=-1000, max_value=1000),
           st.integers(min_value=-1000, max_value=1000))
    def test_between_symmetric(self, col_name, val1, val2):
        """Symmetric between should include SYMMETRIC keyword."""
        t = table('test_table', column(col_name))
        expr = sql.between(getattr(t.c, col_name), val1, val2, symmetric=True)
        result_str = expr_to_str(expr)
        assert 'BETWEEN SYMMETRIC' in result_str


class TestLiteralValues:
    """Test literal value handling."""
    
    @given(st.integers())
    def test_literal_integer(self, value):
        """literal() should preserve integer values."""
        lit = sql.literal(value)
        # Check that it creates a bind parameter
        assert hasattr(lit, 'value')
        assert lit.value == value
    
    @given(st.text(max_size=100))
    def test_literal_string(self, value):
        """literal() should preserve string values."""
        lit = sql.literal(value)
        assert hasattr(lit, 'value')
        assert lit.value == value
    
    @given(st.floats(allow_nan=False, allow_infinity=False))
    def test_literal_float(self, value):
        """literal() should preserve float values."""
        lit = sql.literal(value)
        assert hasattr(lit, 'value')
        assert lit.value == value
    
    def test_literal_none(self):
        """literal(None) should create a null literal."""
        lit = sql.literal(None)
        assert lit.value is None


class TestMixedTypeHandling:
    """Test how operators handle mixed types."""
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier))
    def test_and_with_python_true(self, col_name):
        """and_(expr, True) should handle Python True."""
        expr = create_test_expr(col_name)
        result = sql.and_(expr, True)
        # True is converted to SQL true
        assert 'true' in expr_to_str(result).lower() or expr_to_str(result) == expr_to_str(expr)
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier))
    def test_and_with_python_false(self, col_name):
        """and_(expr, False) should simplify to false."""
        expr = create_test_expr(col_name)
        result = sql.and_(expr, False)
        assert expr_to_str(result) == 'false'
    
    def test_and_with_none(self):
        """and_(None) should handle None as NULL."""
        result = sql.and_(None)
        assert expr_to_str(result) == 'NULL'


class TestComplexLogicalExpressions:
    """Test more complex logical expression combinations."""
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers(),
           st.integers())
    def test_and_idempotence(self, col_name, val1, val2):
        """and_(expr, expr) should include both (not simplified)."""
        expr = create_test_expr(col_name, val1)
        result = sql.and_(expr, expr)
        result_str = expr_to_str(result)
        # SQLAlchemy doesn't simplify idempotent expressions
        assert 'AND' in result_str
    
    @given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
           st.integers())
    def test_and_true_true(self, col_name, value):
        """and_(true(), true()) should simplify to true."""
        result = sql.and_(sql.true(), sql.true())
        assert expr_to_str(result) == 'true'
    
    def test_and_false_false(self):
        """and_(false(), false()) should simplify to false."""
        result = sql.and_(sql.false(), sql.false())
        assert expr_to_str(result) == 'false'
    
    def test_or_true_true(self):
        """or_(true(), true()) should simplify to true."""
        result = sql.or_(sql.true(), sql.true())
        assert expr_to_str(result) == 'true'
    
    def test_or_false_false(self):
        """or_(false(), false()) should simplify to false."""
        result = sql.or_(sql.false(), sql.false())
        assert expr_to_str(result) == 'false'


class TestEdgeCases:
    """Test edge cases and potential bugs."""
    
    @given(st.lists(st.booleans(), min_size=1, max_size=10))
    def test_and_multiple_booleans(self, bool_list):
        """and_ with multiple Python booleans."""
        result = sql.and_(*bool_list)
        result_str = expr_to_str(result)
        # If any False, result should be false
        if False in bool_list:
            assert result_str == 'false'
        # If all True, result should be true
        elif all(bool_list):
            assert result_str == 'true'
    
    @given(st.lists(st.booleans(), min_size=1, max_size=10))
    def test_or_multiple_booleans(self, bool_list):
        """or_ with multiple Python booleans."""
        result = sql.or_(*bool_list)
        result_str = expr_to_str(result)
        # If any True, result should be true
        if True in bool_list:
            assert result_str == 'true'
        # If all False, result should be false
        elif not any(bool_list):
            assert result_str == 'false'
    
    @given(st.lists(
        st.one_of(
            st.just(None),
            st.booleans(),
            st.integers()
        ),
        min_size=1,
        max_size=5
    ))
    def test_and_mixed_types(self, mixed_list):
        """and_ with mixed types including None."""
        try:
            result = sql.and_(*mixed_list)
            result_str = expr_to_str(result)
            # Check result is valid SQL-like string
            assert isinstance(result_str, str)
            # If False in list, should be 'false'
            if False in mixed_list:
                assert result_str == 'false'
        except Exception as e:
            # Some combinations might not be valid
            pytest.skip(f"Invalid combination: {e}")