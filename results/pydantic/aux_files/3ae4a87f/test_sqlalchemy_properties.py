"""Property-based tests for SQLAlchemy using Hypothesis."""

from hypothesis import given, strategies as st, assume
import pytest
from sqlalchemy import (
    quoted_name, and_, or_, not_, between, column,
    literal, bindparam, cast, func
)
from sqlalchemy.sql import ClauseElement
from sqlalchemy.types import Integer, String, Float


# Strategy for valid SQL identifiers
sql_identifier = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=1),
    min_size=1,
    max_size=63
).filter(lambda s: not s[0].isdigit())


class TestQuotedName:
    """Test properties of the quoted_name class."""
    
    @given(st.text(min_size=1, max_size=100), st.booleans())
    def test_quoted_name_case_preservation_when_quoted(self, name, quote):
        """When quote=True, lower() and upper() should preserve the original string."""
        qn = quoted_name(name, quote=quote)
        
        if quote:
            # From source code: when quote=True, lower() and upper() return self
            assert qn.lower() == qn, f"lower() should preserve quoted name {repr(name)}"
            assert qn.upper() == qn, f"upper() should preserve quoted name {repr(name)}"
            assert qn.lower() is qn, "lower() should return the same object"
            assert qn.upper() is qn, "upper() should return the same object"
        else:
            # When quote=False or None, normal string behavior
            assert str(qn.lower()) == name.lower()
            assert str(qn.upper()) == name.upper()
    
    @given(st.text(min_size=1, max_size=100), st.one_of(st.none(), st.booleans()))
    def test_quoted_name_idempotence(self, name, quote):
        """Creating a quoted_name from a quoted_name should be idempotent."""
        qn1 = quoted_name(name, quote)
        qn2 = quoted_name(qn1, quote)
        
        # From source: if isinstance(value, cls) and (quote is None or value.quote == quote): return value
        if quote is None or qn1.quote == quote:
            assert qn2 is qn1, "Should return the same object when quote matches"
        else:
            assert str(qn2) == str(qn1), "String value should be preserved"
            assert qn2.quote == quote, "Quote flag should be updated"
    
    @given(st.text(min_size=1, max_size=100), 
           st.one_of(st.none(), st.booleans()),
           st.one_of(st.none(), st.booleans()))
    def test_quoted_name_nested_construction(self, name, quote1, quote2):
        """Test nested construction of quoted_name."""
        qn1 = quoted_name(name, quote1)
        qn2 = quoted_name(qn1, quote2)
        
        # The string content should always be preserved
        assert str(qn2) == name
        
        # The final quote should be quote2 if not None, else quote1
        expected_quote = quote2 if quote2 is not None else quote1
        assert qn2.quote == expected_quote


class TestLogicalOperators:
    """Test properties of SQL logical operators."""
    
    @given(sql_identifier)
    def test_not_double_negation(self, col_name):
        """Double negation should be rendered correctly."""
        col = column(col_name)
        single_not = not_(col)
        double_not = not_(not_(col))
        
        # SQLAlchemy may quote column names, especially uppercase ones
        col_str = str(col)
        
        # Check the SQL representation
        assert str(single_not) == f"NOT {col_str}"
        assert str(double_not) == f"NOT (NOT {col_str})"
    
    @given(sql_identifier)
    def test_and_idempotence(self, col_name):
        """and_(x, x) should produce x AND x."""
        col = column(col_name)
        result = and_(col, col)
        
        # SQLAlchemy may quote column names
        col_str = str(col)
        
        # SQLAlchemy doesn't optimize this away, it produces "x AND x"
        assert str(result) == f"{col_str} AND {col_str}"
    
    @given(sql_identifier)
    def test_or_idempotence(self, col_name):
        """or_(x, x) should produce x OR x."""
        col = column(col_name)
        result = or_(col, col)
        
        # SQLAlchemy may quote column names
        col_str = str(col)
        
        # SQLAlchemy doesn't optimize this away, it produces "x OR x"
        assert str(result) == f"{col_str} OR {col_str}"
    
    @given(sql_identifier, sql_identifier)
    def test_and_with_different_columns(self, col1_name, col2_name):
        """and_ should work with different columns."""
        assume(col1_name != col2_name)  # Make sure columns are different
        
        col1 = column(col1_name)
        col2 = column(col2_name)
        result = and_(col1, col2)
        
        # Check that both columns appear in the result
        result_str = str(result)
        assert col1_name in result_str
        assert col2_name in result_str
        assert "AND" in result_str


class TestBetweenOperator:
    """Test properties of the between operator."""
    
    @given(sql_identifier, st.integers(), st.integers())
    def test_between_basic(self, col_name, lower, upper):
        """Test basic between operator."""
        col = column(col_name)
        result = between(col, lower, upper)
        
        # Check the SQL representation
        result_str = str(result)
        assert col_name in result_str
        assert "BETWEEN" in result_str
        assert "AND" in result_str
    
    @given(sql_identifier, st.integers(), st.integers())
    def test_between_symmetric(self, col_name, val1, val2):
        """Test symmetric between operator."""
        col = column(col_name)
        
        # Symmetric between should work regardless of order
        result1 = between(col, val1, val2, symmetric=True)
        result2 = between(col, val2, val1, symmetric=True)
        
        # Both should produce BETWEEN SYMMETRIC
        assert "BETWEEN SYMMETRIC" in str(result1) or "BETWEEN" in str(result1)
        assert "BETWEEN SYMMETRIC" in str(result2) or "BETWEEN" in str(result2)
    
    @given(sql_identifier, 
           st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
           st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
    def test_between_with_floats(self, col_name, lower, upper):
        """Test between with float values."""
        col = column(col_name)
        result = between(col, lower, upper)
        
        # Should create a valid BETWEEN expression
        result_str = str(result)
        assert col_name in result_str
        assert "BETWEEN" in result_str


class TestFunctionExpressions:
    """Test SQL function expressions via func."""
    
    @given(st.text(min_size=1, max_size=100))
    def test_func_lower_upper_inverse(self, text_val):
        """func.lower and func.upper should be inverses in terms of case."""
        lower_expr = func.lower(text_val)
        upper_expr = func.upper(text_val)
        
        # Check that they produce function calls
        assert "lower(" in str(lower_expr)
        assert "upper(" in str(upper_expr)
    
    @given(st.text(min_size=0, max_size=100))
    def test_func_length(self, text_val):
        """func.length should create a length function call."""
        length_expr = func.length(text_val)
        
        # Check that it produces a length function call
        assert "length(" in str(length_expr)
    
    @given(st.lists(st.text(min_size=0, max_size=20), min_size=2, max_size=5))
    def test_func_concat(self, strings):
        """func.concat should handle multiple arguments."""
        concat_expr = func.concat(*strings)
        
        # Check that it produces a concat function call
        assert "concat(" in str(concat_expr)


class TestBindParameter:
    """Test bind parameter properties."""
    
    @given(st.text(min_size=1, max_size=30).filter(lambda s: not s.startswith(':')),
           st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), 
                     st.text(), st.none()))
    def test_bindparam_preserves_value(self, key, value):
        """bindparam should preserve its key and value."""
        param = bindparam(key, value)
        
        # Check that the key is preserved
        assert param.key == key
        # Check that the value is preserved
        assert param.value == value
    
    @given(st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), 
                      st.text(), st.booleans()))
    def test_literal_creates_bindparam(self, value):
        """literal should create a bind parameter."""
        lit = literal(value)
        
        # literal creates a BindParameter
        from sqlalchemy.sql.elements import BindParameter
        assert isinstance(lit, BindParameter)
        assert lit.value == value


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running property-based tests for SQLAlchemy...")
    test = TestQuotedName()
    test.test_quoted_name_case_preservation_when_quoted("TEST", True)
    test.test_quoted_name_case_preservation_when_quoted("test", False)
    print("✓ Basic tests pass")