"""Property-based tests for pydantic.experimental module."""

import re
from typing import Annotated
from hypothesis import given, strategies as st, assume, settings
import pytest
from pydantic import BaseModel, ValidationError
from pydantic.experimental.pipeline import transform, validate_as, _Pipeline


@given(st.text())
def test_str_lower_idempotence(s: str):
    """Test that str_lower is idempotent: lower(lower(x)) = lower(x)"""
    
    class Model(BaseModel):
        value: Annotated[str, validate_as(str).str_lower()]
    
    # Apply once
    result1 = Model(value=s).value
    # Apply twice (by passing the result through again)
    result2 = Model(value=result1).value
    
    assert result1 == result2, f"str_lower not idempotent: {result1!r} != {result2!r}"


@given(st.text())
def test_str_upper_idempotence(s: str):
    """Test that str_upper is idempotent: upper(upper(x)) = upper(x)"""
    
    class Model(BaseModel):
        value: Annotated[str, validate_as(str).str_upper()]
    
    # Apply once
    result1 = Model(value=s).value
    # Apply twice
    result2 = Model(value=result1).value
    
    assert result1 == result2, f"str_upper not idempotent: {result1!r} != {result2!r}"


@given(st.text())
def test_str_strip_idempotence(s: str):
    """Test that str_strip is idempotent: strip(strip(x)) = strip(x)"""
    
    class Model(BaseModel):
        value: Annotated[str, validate_as(str).str_strip()]
    
    # Apply once
    result1 = Model(value=s).value
    # Apply twice
    result2 = Model(value=result1).value
    
    assert result1 == result2, f"str_strip not idempotent: {result1!r} != {result2!r}"


@given(st.text())
def test_str_upper_lower_relationship(s: str):
    """Test that upper and lower have the expected relationship"""
    
    class LowerModel(BaseModel):
        value: Annotated[str, validate_as(str).str_lower()]
    
    class UpperModel(BaseModel):
        value: Annotated[str, validate_as(str).str_upper()]
    
    lower_result = LowerModel(value=s).value
    upper_result = UpperModel(value=s).value
    
    # Check that converting upper result to lower equals lower result
    assert upper_result.lower() == lower_result
    # Check that converting lower result to upper equals upper result
    assert lower_result.upper() == upper_result


@given(st.integers(), st.integers())
def test_gt_lt_mutually_exclusive(value: int, threshold: int):
    """Test that gt and lt constraints are mutually exclusive for the same threshold"""
    assume(value != threshold)  # Skip when equal
    
    class GtModel(BaseModel):
        value: Annotated[int, validate_as(int).gt(threshold)]
    
    class LtModel(BaseModel):
        value: Annotated[int, validate_as(int).lt(threshold)]
    
    # Exactly one should pass
    gt_passes = False
    lt_passes = False
    
    try:
        GtModel(value=value)
        gt_passes = True
    except ValidationError:
        pass
    
    try:
        LtModel(value=value)
        lt_passes = True
    except ValidationError:
        pass
    
    # Exactly one should pass (XOR)
    assert gt_passes != lt_passes, f"Both or neither passed for value={value}, threshold={threshold}"


@given(st.integers(), st.integers())
def test_ge_le_coverage(value: int, threshold: int):
    """Test that ge and le together cover all integers"""
    
    class GeModel(BaseModel):
        value: Annotated[int, validate_as(int).ge(threshold)]
    
    class LeModel(BaseModel):
        value: Annotated[int, validate_as(int).le(threshold)]
    
    ge_passes = False
    le_passes = False
    
    try:
        GeModel(value=value)
        ge_passes = True
    except ValidationError:
        pass
    
    try:
        LeModel(value=value)
        le_passes = True
    except ValidationError:
        pass
    
    # At least one should pass (they overlap at threshold)
    assert ge_passes or le_passes, f"Neither ge nor le passed for value={value}, threshold={threshold}"


@given(st.integers(), st.integers())
def test_eq_not_eq_inverse(value: int, target: int):
    """Test that eq and not_eq are inverses"""
    
    class EqModel(BaseModel):
        value: Annotated[int, validate_as(int).eq(target)]
    
    class NotEqModel(BaseModel):
        value: Annotated[int, validate_as(int).not_eq(target)]
    
    eq_passes = False
    not_eq_passes = False
    
    try:
        EqModel(value=value)
        eq_passes = True
    except ValidationError:
        pass
    
    try:
        NotEqModel(value=value)
        not_eq_passes = True
    except ValidationError:
        pass
    
    # Exactly one should pass (XOR)
    assert eq_passes != not_eq_passes, f"eq and not_eq both {eq_passes} for value={value}, target={target}"


@given(st.integers(), st.lists(st.integers(), min_size=1))
def test_in_not_in_inverse(value: int, values: list[int]):
    """Test that in_ and not_in are inverses"""
    
    class InModel(BaseModel):
        value: Annotated[int, validate_as(int).in_(values)]
    
    class NotInModel(BaseModel):
        value: Annotated[int, validate_as(int).not_in(values)]
    
    in_passes = False
    not_in_passes = False
    
    try:
        InModel(value=value)
        in_passes = True
    except ValidationError:
        pass
    
    try:
        NotInModel(value=value)
        not_in_passes = True
    except ValidationError:
        pass
    
    # Exactly one should pass (XOR)
    assert in_passes != not_in_passes, f"in_ and not_in both {in_passes} for value={value} in {values}"


@given(st.integers(min_value=-1000, max_value=1000), st.integers(min_value=1, max_value=100))
def test_multiple_of_property(value: int, divisor: int):
    """Test that multiple_of constraint works correctly"""
    
    class MultipleOfModel(BaseModel):
        value: Annotated[int, validate_as(int).multiple_of(divisor)]
    
    should_pass = (value % divisor == 0)
    
    try:
        result = MultipleOfModel(value=value)
        assert should_pass, f"multiple_of({divisor}) accepted {value} but {value} % {divisor} = {value % divisor}"
        assert result.value == value
    except ValidationError:
        assert not should_pass, f"multiple_of({divisor}) rejected {value} but {value} % {divisor} = 0"


@given(st.text(min_size=1))
def test_str_pattern_basic(s: str):
    """Test that str_pattern correctly matches patterns"""
    # Test with a simple pattern that matches everything
    class AnyModel(BaseModel):
        value: Annotated[str, validate_as(str).str_pattern('.*')]
    
    # This should always pass
    result = AnyModel(value=s)
    assert result.value == s
    
    # Test with a pattern that never matches (impossible character class)
    # Using an impossible pattern without lookahead
    class NeverMatchModel(BaseModel):
        value: Annotated[str, validate_as(str).str_pattern('[^\x00-\xff]+')]  # Matches no ASCII/extended ASCII chars
    
    # For ASCII strings, this should always fail
    if all(ord(c) <= 255 for c in s):
        with pytest.raises(ValidationError):
            NeverMatchModel(value=s)


@given(st.text())
def test_str_contains_property(s: str):
    """Test str_contains with substrings of the input"""
    assume(len(s) > 0)
    
    # Pick a substring that's definitely in s
    start = len(s) // 4
    end = start + max(1, len(s) // 2)
    substring = s[start:end]
    
    class ContainsModel(BaseModel):
        value: Annotated[str, validate_as(str).str_contains(substring)]
    
    # Should pass since substring is from s
    result = ContainsModel(value=s)
    assert result.value == s


@given(st.text(min_size=1))
def test_str_starts_ends_with(s: str):
    """Test str_starts_with and str_ends_with"""
    
    # Test starts_with with actual prefix
    prefix = s[0]
    class StartsModel(BaseModel):
        value: Annotated[str, validate_as(str).str_starts_with(prefix)]
    
    result = StartsModel(value=s)
    assert result.value == s
    
    # Test ends_with with actual suffix
    suffix = s[-1]
    class EndsModel(BaseModel):
        value: Annotated[str, validate_as(str).str_ends_with(suffix)]
    
    result = EndsModel(value=s)
    assert result.value == s


@given(st.lists(st.text(), min_size=0, max_size=10))
def test_len_constraint(items: list[str]):
    """Test len constraint on lists"""
    length = len(items)
    
    # Test exact length bounds
    class ExactLenModel(BaseModel):
        value: Annotated[list[str], validate_as(list[str]).len(length, length)]
    
    result = ExactLenModel(value=items)
    assert result.value == items
    
    # Test minimum length
    if length > 0:
        class MinLenModel(BaseModel):
            value: Annotated[list[str], validate_as(list[str]).len(length - 1)]
        
        result = MinLenModel(value=items)
        assert result.value == items
    
    # Test maximum length  
    class MaxLenModel(BaseModel):
        value: Annotated[list[str], validate_as(list[str]).len(0, length + 1)]
    
    result = MaxLenModel(value=items)
    assert result.value == items


@given(st.integers())
def test_transform_composition(x: int):
    """Test that multiple transformations compose correctly"""
    
    # Define transformations
    def add_one(v: int) -> int:
        return v + 1
    
    def multiply_two(v: int) -> int:
        return v * 2
    
    class TransformModel(BaseModel):
        value: Annotated[int, transform(add_one).transform(multiply_two)]
    
    result = TransformModel(value=x)
    # Should be (x + 1) * 2
    expected = (x + 1) * 2
    assert result.value == expected, f"Transform composition failed: got {result.value}, expected {expected}"


@given(st.floats(min_value=-1e6, max_value=1e6))
def test_constraint_chaining(x: float):
    """Test that multiple constraints can be chained"""
    assume(-100 <= x <= 100)  # Focus on reasonable range
    
    class ChainedModel(BaseModel):
        value: Annotated[float, validate_as(float).ge(-100).le(100)]
    
    # Should pass for values in range
    result = ChainedModel(value=x)
    assert result.value == x
    
    # Test that values outside range fail
    class StrictModel(BaseModel):
        value: Annotated[float, validate_as(float).gt(-100).lt(100)]
    
    if x == -100 or x == 100:
        with pytest.raises(ValidationError):
            StrictModel(value=x)
    else:
        result = StrictModel(value=x)
        assert result.value == x


@given(st.integers(min_value=-1000, max_value=1000))
def test_otherwise_operator(x: int):
    """Test the otherwise (|) operator for fallback validation"""
    
    # Create a pipeline that accepts positive or negative but not zero
    pipeline = validate_as(int).gt(0) | validate_as(int).lt(0)
    
    class OrModel(BaseModel):
        value: Annotated[int, pipeline]
    
    if x == 0:
        with pytest.raises(ValidationError):
            OrModel(value=x)
    else:
        result = OrModel(value=x)
        assert result.value == x


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running property-based tests for pydantic.experimental...")
    pytest.main([__file__, "-v"])