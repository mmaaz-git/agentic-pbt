"""Property-based tests for troposphere.route53resolver module"""

import math
from hypothesis import given, strategies as st, assume
import pytest
import troposphere.route53resolver as r53r


# Test 1: integer function should only accept values that are actual integers
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_rejects_floats_with_decimal_parts(x):
    """The integer() function should reject floats with decimal parts"""
    assume(not x.is_integer())  # Only test non-integer floats
    
    # The function should reject floats with decimal parts
    with pytest.raises(ValueError, match="is not a valid integer"):
        r53r.integer(x)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_accepts_whole_number_floats(x):
    """The integer() function should handle floats that are whole numbers"""
    assume(x.is_integer())
    
    # This should work since the float represents a whole number
    result = r53r.integer(x)
    assert result == x


@given(st.booleans())
def test_integer_handles_booleans(b):
    """The integer() function accepts booleans (inherits from int in Python)"""
    # In Python, bool inherits from int, so this actually works
    # True -> 1, False -> 0
    result = r53r.integer(b)
    assert result == b
    

@given(st.text(min_size=1).filter(lambda x: not x.strip().lstrip('-').isdigit()))
def test_integer_rejects_non_numeric_strings(s):
    """The integer() function should reject non-numeric strings"""
    with pytest.raises(ValueError, match="is not a valid integer"):
        r53r.integer(s)


@given(st.one_of(st.lists(st.integers()), st.dictionaries(st.text(), st.integers()), st.tuples(st.integers())))
def test_integer_rejects_collections(collection):
    """The integer() function should reject collections"""
    with pytest.raises(ValueError, match="is not a valid integer"):
        r53r.integer(collection)


# Test 2: validate_ruletype invariants
@given(st.text())
def test_validate_ruletype_accepts_only_valid_types(ruletype):
    """validate_ruletype should only accept 'SYSTEM' or 'FORWARD'"""
    if ruletype in ('SYSTEM', 'FORWARD'):
        result = r53r.validate_ruletype(ruletype)
        assert result == ruletype
    else:
        with pytest.raises(ValueError, match="Rule type must be one of"):
            r53r.validate_ruletype(ruletype)


@given(st.sampled_from(['system', 'forward', 'System', 'Forward', 'SYSTEM', 'FORWARD']))
def test_validate_ruletype_case_sensitivity(ruletype):
    """validate_ruletype should be case-sensitive"""
    if ruletype in ('SYSTEM', 'FORWARD'):
        result = r53r.validate_ruletype(ruletype)
        assert result == ruletype
    else:
        with pytest.raises(ValueError, match="Rule type must be one of"):
            r53r.validate_ruletype(ruletype)


@given(st.one_of(st.none(), st.integers(), st.floats(), st.lists(st.text())))
def test_validate_ruletype_rejects_non_strings(value):
    """validate_ruletype should reject non-string values"""
    with pytest.raises(ValueError, match="Rule type must be one of"):
        r53r.validate_ruletype(value)


# Test 3: ResolverRule class property validation
@given(st.text())
def test_resolver_rule_validates_ruletype_property(ruletype):
    """ResolverRule.RuleType property should validate using validate_ruletype"""
    rule = r53r.ResolverRule('TestRule')
    
    if ruletype in ('SYSTEM', 'FORWARD'):
        rule.RuleType = ruletype
        assert rule.RuleType == ruletype
        # Verify it appears in to_dict output
        result = rule.to_dict()
        assert result['Properties']['RuleType'] == ruletype
    else:
        with pytest.raises(ValueError):
            rule.RuleType = ruletype


# Test 4: Round-trip property - setting and getting properties
@given(st.sampled_from(['SYSTEM', 'FORWARD']))
def test_resolver_rule_roundtrip_property(ruletype):
    """Setting and getting RuleType should preserve the value"""
    rule = r53r.ResolverRule('TestRule')
    rule.RuleType = ruletype
    assert rule.RuleType == ruletype
    
    # Should also survive serialization
    dict_form = rule.to_dict()
    assert dict_form['Properties']['RuleType'] == ruletype


# Test 5: Property consistency across instances
@given(st.sampled_from(['SYSTEM', 'FORWARD']), st.sampled_from(['SYSTEM', 'FORWARD']))
def test_resolver_rule_instances_independent(type1, type2):
    """Different ResolverRule instances should have independent properties"""
    rule1 = r53r.ResolverRule('Rule1')
    rule2 = r53r.ResolverRule('Rule2')
    
    rule1.RuleType = type1
    rule2.RuleType = type2
    
    assert rule1.RuleType == type1
    assert rule2.RuleType == type2
    assert rule1.title == 'Rule1'
    assert rule2.title == 'Rule2'