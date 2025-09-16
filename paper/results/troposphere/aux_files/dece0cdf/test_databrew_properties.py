#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.databrew as databrew
from troposphere import validators
from troposphere import BaseAWSObject
import pytest
import math

# Test 1: Boolean validator round-trip property
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_valid_inputs(value):
    """Boolean validator should correctly convert valid boolean representations"""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    
    # Property: True values always convert to True
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    # Property: False values always convert to False
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False

@given(st.one_of(
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.floats(allow_nan=True, allow_infinity=True),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Boolean validator should raise ValueError for non-boolean representations"""
    with pytest.raises(ValueError):
        validators.boolean(value)

# Test 2: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.lstrip('-').isdigit())
))
def test_integer_validator_valid(value):
    """Integer validator should accept anything int() accepts"""
    result = validators.integer(value)
    # Property: the result should be convertible to int
    int(result)  # Should not raise

@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).filter(lambda x: not x.is_integer() if not math.isnan(x) and not math.isinf(x) else True),
    st.text().filter(lambda x: not x.lstrip('-').isdigit() and x != ""),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_invalid(value):
    """Integer validator should raise ValueError for non-integer values"""
    assume(value != "")  # Empty string edge case
    with pytest.raises(ValueError):
        validators.integer(value)

# Test 3: Double validator property
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: _is_float_string(x))
))
def test_double_validator_valid(value):
    """Double validator should accept anything float() accepts"""
    result = validators.double(value)
    # Property: the result should be convertible to float
    float(result)  # Should not raise

def _is_float_string(s):
    """Helper to check if string is convertible to float"""
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False

@given(st.one_of(
    st.text().filter(lambda x: not _is_float_string(x) and x != ""),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_double_validator_invalid(value):
    """Double validator should raise ValueError for non-float values"""
    assume(value != "")  # Empty string edge case
    with pytest.raises(ValueError):
        validators.double(value)

# Test 4: Positive integer validator property
@given(st.integers(min_value=0))
def test_positive_integer_validator_accepts_positive(value):
    """Positive integer validator should accept non-negative integers"""
    result = validators.positive_integer(value)
    assert result == value

@given(st.integers(max_value=-1))
def test_positive_integer_validator_rejects_negative(value):
    """Positive integer validator should reject negative integers"""
    with pytest.raises(ValueError, match="is not a positive integer"):
        validators.positive_integer(value)

# Test 5: Property validation in AWS objects
@given(
    st.text(min_size=1),  # bucket name
    st.one_of(st.none(), st.text())  # optional key
)
def test_s3location_property_validation(bucket, key):
    """S3Location should validate required and optional properties correctly"""
    # S3Location requires 'Bucket' and optionally accepts 'Key'
    loc = databrew.S3Location(Bucket=bucket)
    
    # Property: Required field is set
    assert loc.Bucket == bucket
    
    # Property: Optional field can be set
    if key is not None:
        loc.Key = key
        assert loc.Key == key
    
    # Property: to_dict should include all set properties
    d = loc.to_dict()
    assert d["Bucket"] == bucket
    if key is not None:
        assert d["Key"] == key
    else:
        assert "Key" not in d

# Test 6: FilesLimit MaxFiles validation
@given(st.integers())
def test_fileslimit_maxfiles_validation(max_files):
    """FilesLimit should validate MaxFiles as an integer"""
    # MaxFiles is required and should be validated as integer
    if isinstance(max_files, int):
        limit = databrew.FilesLimit(MaxFiles=max_files)
        assert limit.MaxFiles == max_files
    else:
        # This test is actually always passing since we only generate integers
        # But the validator should handle the conversion
        pass

# Test 7: Integer range validator
@given(st.integers())
def test_integer_range_validator(value):
    """Integer range validator should enforce min/max bounds"""
    min_val, max_val = -10, 10
    range_validator = validators.integer_range(min_val, max_val)
    
    if min_val <= value <= max_val:
        result = range_validator(value)
        assert result == value
    else:
        with pytest.raises(ValueError, match="Integer must be between"):
            range_validator(value)

# Test 8: SheetIndexes list property 
@given(st.lists(st.integers(), min_size=0, max_size=10))
def test_exceloptions_sheetindexes_list(indexes):
    """ExcelOptions SheetIndexes should accept list of integers"""
    options = databrew.ExcelOptions()
    options.SheetIndexes = indexes
    assert options.SheetIndexes == indexes
    
    # Property: to_dict should preserve the list
    d = options.to_dict()
    if indexes:
        assert d["SheetIndexes"] == indexes

# Test 9: Boolean property in AWS objects
@given(st.one_of(
    st.booleans(),
    st.sampled_from([0, 1, "true", "True", "false", "False"])
))
def test_csv_options_header_row_boolean(value):
    """CsvOptions HeaderRow should use boolean validator"""
    options = databrew.CsvOptions()
    
    # Set the HeaderRow property
    options.HeaderRow = value
    
    # Property: Should be converted to proper boolean
    if value in [True, 1, "1", "true", "True"]:
        assert options.HeaderRow is True
    elif value in [False, 0, "0", "false", "False"]:
        assert options.HeaderRow is False

# Test 10: Required property enforcement
@given(st.text(min_size=1))
def test_rule_required_properties(name):
    """Rule should enforce required properties"""
    # Rule requires both CheckExpression and Name
    check_expr = "test_expression"
    
    rule = databrew.Rule(
        CheckExpression=check_expr,
        Name=name
    )
    
    assert rule.CheckExpression == check_expr
    assert rule.Name == name
    
    # Property: to_dict should include all required properties
    d = rule.to_dict()
    assert d["CheckExpression"] == check_expr
    assert d["Name"] == name

if __name__ == "__main__":
    # Run a quick smoke test
    print("Running property tests...")
    test_boolean_validator_valid_inputs()
    test_integer_validator_valid()
    test_double_validator_valid()
    test_positive_integer_validator_accepts_positive()
    test_s3location_property_validation()
    print("Basic tests passed!")