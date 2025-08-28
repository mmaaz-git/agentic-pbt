"""Additional property-based tests targeting potential bugs in pydantic.experimental."""

import re
from typing import Annotated
from hypothesis import given, strategies as st, assume, settings, example
import pytest
from pydantic import BaseModel, ValidationError
from pydantic.experimental.pipeline import transform, validate_as, _Pipeline


@given(st.floats())
def test_ge_constraint_boundary(value: float):
    """Test ge constraint with boundary values including NaN and inf"""
    
    class GeModel(BaseModel):
        field: Annotated[float, validate_as(float).ge(0.0)]
    
    if value >= 0.0 or str(value) == 'nan':  # NaN comparisons are always False
        if str(value) != 'nan':
            result = GeModel(field=value)
            assert result.field == value
        else:
            # NaN should fail the >= 0 check
            with pytest.raises(ValidationError):
                GeModel(field=value)
    else:
        with pytest.raises(ValidationError):
            GeModel(field=value)


@given(st.integers(min_value=-1000, max_value=1000))
def test_chained_constraints_order(x: int):
    """Test that chained constraints are applied correctly"""
    
    # Chain multiple constraints
    class ChainModel(BaseModel):
        value: Annotated[int, validate_as(int).ge(0).le(100).multiple_of(5)]
    
    should_pass = (0 <= x <= 100) and (x % 5 == 0)
    
    if should_pass:
        result = ChainModel(value=x)
        assert result.value == x
    else:
        with pytest.raises(ValidationError):
            ChainModel(value=x)


@given(st.text())
def test_str_title_property(s: str):
    """Test str_title transformation"""
    
    class TitleModel(BaseModel):
        value: Annotated[str, validate_as(str).str_title()]
    
    result = TitleModel(value=s)
    assert result.value == s.title()


@given(st.lists(st.integers()))
def test_len_constraint_edge_cases(items: list[int]):
    """Test len constraint with edge cases"""
    
    # Test min_len = 0
    class MinZeroModel(BaseModel):
        value: Annotated[list[int], validate_as(list[int]).len(0)]
    
    # Should always pass
    result = MinZeroModel(value=items)
    assert result.value == items
    
    # Test exact length match
    if len(items) > 0:
        class ExactModel(BaseModel):
            value: Annotated[list[int], validate_as(list[int]).len(len(items), len(items))]
        
        result = ExactModel(value=items)
        assert result.value == items


@given(st.text())
def test_empty_pattern_match(s: str):
    """Test pattern matching with empty pattern"""
    
    # Empty pattern should match empty string at every position
    class EmptyPatternModel(BaseModel):
        value: Annotated[str, validate_as(str).str_pattern('')]
    
    # Empty pattern matches everything
    result = EmptyPatternModel(value=s)
    assert result.value == s


@given(st.integers())
def test_otherwise_with_same_type(x: int):
    """Test otherwise operator with overlapping conditions"""
    
    # Create overlapping pipelines
    pipeline = validate_as(int).ge(0).le(10) | validate_as(int).ge(5).le(15)
    
    class OrModel(BaseModel):
        value: Annotated[int, pipeline]
    
    # Should pass if in either range [0, 10] or [5, 15] = [0, 15]
    if 0 <= x <= 15:
        result = OrModel(value=x)
        assert result.value == x
    else:
        with pytest.raises(ValidationError):
            OrModel(value=x)


@given(st.floats(min_value=-1e10, max_value=1e10))
def test_multiple_of_float(value: float):
    """Test multiple_of with float values"""
    assume(not (str(value) in ['nan', 'inf', '-inf']))
    
    divisor = 0.5
    
    class MultipleOfFloatModel(BaseModel):
        field: Annotated[float, validate_as(float).multiple_of(divisor)]
    
    # Check if value is a multiple of divisor (within floating point precision)
    remainder = abs(value % divisor)
    # Account for floating point precision
    is_multiple = remainder < 1e-10 or abs(remainder - divisor) < 1e-10
    
    if is_multiple:
        result = MultipleOfFloatModel(field=value)
        assert result.field == value
    else:
        with pytest.raises(ValidationError):
            MultipleOfFloatModel(field=value)


@given(st.text(alphabet=st.characters(whitelist_categories=('Zs', 'Cc'))))
def test_str_strip_with_various_whitespace(s: str):
    """Test str_strip with various Unicode whitespace characters"""
    
    class StripModel(BaseModel):
        value: Annotated[str, validate_as(str).str_strip()]
    
    result = StripModel(value=s)
    # After stripping whitespace, should be empty
    assert result.value == s.strip()
    assert result.value == ""


@given(st.text())
def test_predicate_constraint(s: str):
    """Test custom predicate constraints"""
    
    def has_even_length(v: str) -> bool:
        return len(v) % 2 == 0
    
    class PredicateModel(BaseModel):
        value: Annotated[str, validate_as(str).predicate(has_even_length)]
    
    if len(s) % 2 == 0:
        result = PredicateModel(value=s)
        assert result.value == s
    else:
        with pytest.raises(ValidationError):
            PredicateModel(value=s)


@given(st.text(min_size=1))
def test_str_contains_empty_string(s: str):
    """Test str_contains with empty substring"""
    
    # Every string contains the empty string
    class ContainsEmptyModel(BaseModel):
        value: Annotated[str, validate_as(str).str_contains('')]
    
    result = ContainsEmptyModel(value=s)
    assert result.value == s


@given(st.lists(st.integers(), min_size=1))
def test_pipeline_and_operator(items: list[int]):
    """Test the then (&) operator for sequential validation"""
    
    # First validate as list, then transform to get length, then validate as int > 0
    pipeline = validate_as(list[int]) & validate_as(list[int]).transform(len).validate_as(int).gt(0)
    
    class AndModel(BaseModel):
        value: Annotated[list[int], pipeline]
    
    # This is testing a complex pipeline, but the transform changes the type
    # which might not work as expected with BaseModel field typing
    # Let's test a simpler case
    
    # Actually, the & operator chains validations, not transforms the value type
    # So let's test constraint chaining instead
    simple_pipeline = validate_as(list[int]).len(1, 100) & validate_as(list[int]).len(0, 50)
    
    class SimpleAndModel(BaseModel):
        value: Annotated[list[int], simple_pipeline]
    
    # Should only accept lists with length in intersection [1, 50]
    if 1 <= len(items) <= 50:
        result = SimpleAndModel(value=items)
        assert result.value == items
    else:
        with pytest.raises(ValidationError):
            SimpleAndModel(value=items)


if __name__ == "__main__":
    print("Running additional property-based tests...")
    pytest.main([__file__, "-v", "--tb=short"])