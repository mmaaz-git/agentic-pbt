import math
from hypothesis import assume, given, strategies as st, settings
import troposphere.wafregional as waf
from troposphere.validators import boolean, integer
from troposphere.validators.wafregional import validate_waf_action_type


# Test 1: Boolean validator should handle multiple representations consistently
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_consistency(value):
    result = boolean(value)
    assert isinstance(result, bool)
    
    # Property: All truthy representations should return True
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    # Property: All falsy representations should return False
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


# Test 2: Boolean validator idempotence property
@given(st.sampled_from([True, False]))
def test_boolean_validator_idempotence(value):
    # Property: boolean(boolean(x)) = boolean(x) for valid inputs
    first_result = boolean(value)
    second_result = boolean(first_result)
    assert first_result == second_result


# Test 3: Integer validator should accept various numeric representations
@given(st.one_of(
    st.integers(),
    st.text(alphabet='0123456789', min_size=1),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x.is_integer())
))
def test_integer_validator_accepts_valid_integers(value):
    # For floats that are whole numbers, they should be accepted
    if isinstance(value, float) and value.is_integer():
        result = integer(value)
        assert int(result) == int(value)
    else:
        result = integer(value)
        # Property: The validator should preserve the value's integer representation
        assert int(result) == int(value)


# Test 4: WAF action type validator only accepts specific values
@given(st.text())
def test_waf_action_validator_constraint(action):
    valid_actions = ["ALLOW", "BLOCK", "COUNT"]
    
    if action in valid_actions:
        # Property: Valid actions should be returned unchanged
        result = validate_waf_action_type(action)
        assert result == action
    else:
        # Property: Invalid actions should raise ValueError
        try:
            validate_waf_action_type(action)
            assert False, f"Should have raised ValueError for {action}"
        except ValueError as e:
            assert 'Type must be one of' in str(e)


# Test 5: ByteMatchTuples property validation
@given(
    field_data=st.text(min_size=1),
    field_type=st.text(min_size=1),
    positional_constraint=st.text(min_size=1),
    text_transformation=st.text(min_size=1),
    include_target_string=st.booleans(),
    include_target_string_base64=st.booleans()
)
def test_byte_match_tuples_creation(
    field_data, field_type, positional_constraint, 
    text_transformation, include_target_string, include_target_string_base64
):
    # Property: ByteMatchTuples should accept valid field combinations
    field_to_match = waf.FieldToMatch(
        Data=field_data,
        Type=field_type
    )
    
    props = {
        "FieldToMatch": field_to_match,
        "PositionalConstraint": positional_constraint,
        "TextTransformation": text_transformation
    }
    
    # You can specify either TargetString or TargetStringBase64, but not both
    if include_target_string and not include_target_string_base64:
        props["TargetString"] = "test_string"
    elif include_target_string_base64 and not include_target_string:
        props["TargetStringBase64"] = "dGVzdF9zdHJpbmc="  # base64 of "test_string"
    
    byte_match_tuple = waf.ByteMatchTuples(**props)
    
    # Property: Required fields should be preserved
    assert byte_match_tuple.FieldToMatch == field_to_match
    assert byte_match_tuple.PositionalConstraint == positional_constraint
    assert byte_match_tuple.TextTransformation == text_transformation


# Test 6: IPSetDescriptors Type and Value are required
@given(
    ip_type=st.text(min_size=1),
    ip_value=st.text(min_size=1)
)
def test_ipset_descriptors_required_fields(ip_type, ip_value):
    # Property: IPSetDescriptors must have Type and Value
    descriptor = waf.IPSetDescriptors(
        Type=ip_type,
        Value=ip_value
    )
    
    assert descriptor.Type == ip_type
    assert descriptor.Value == ip_value


# Test 7: RateBasedRule RateLimit must be an integer
@given(
    rate_limit=st.integers(min_value=100, max_value=2000000000),
    metric_name=st.text(min_size=1, max_size=255),
    name=st.text(min_size=1, max_size=128),
    rate_key=st.sampled_from(["IP"])
)
def test_rate_based_rule_rate_limit(rate_limit, metric_name, name, rate_key):
    # Property: RateLimit should accept and preserve integer values
    rule = waf.RateBasedRule(
        MetricName=metric_name,
        Name=name,
        RateKey=rate_key,
        RateLimit=rate_limit
    )
    
    assert rule.RateLimit == rate_limit
    assert rule.MetricName == metric_name
    assert rule.Name == name
    assert rule.RateKey == rate_key


# Test 8: Predicates Negated field accepts boolean
@given(
    data_id=st.text(min_size=1),
    negated=st.one_of(
        st.booleans(),
        st.sampled_from([0, 1, "true", "false", "True", "False"])
    ),
    pred_type=st.text(min_size=1)
)
def test_predicates_negated_boolean(data_id, negated, pred_type):
    # Property: Negated field should handle boolean-like values
    predicate = waf.Predicates(
        DataId=data_id,
        Negated=negated,
        Type=pred_type
    )
    
    assert predicate.DataId == data_id
    assert predicate.Type == pred_type
    # The Negated field uses the boolean validator
    assert hasattr(predicate, 'Negated')


# Test 9: RegexPatternSet requires RegexPatternStrings to be a list
@given(
    name=st.text(min_size=1),
    patterns=st.lists(st.text(min_size=1), min_size=1, max_size=10)
)
def test_regex_pattern_set_list_property(name, patterns):
    # Property: RegexPatternStrings must be a list of strings
    pattern_set = waf.RegexPatternSet(
        Name=name,
        RegexPatternStrings=patterns
    )
    
    assert pattern_set.Name == name
    assert pattern_set.RegexPatternStrings == patterns
    assert isinstance(pattern_set.RegexPatternStrings, list)


# Test 10: Action Type validator in Action class
@given(action_type=st.sampled_from(["ALLOW", "BLOCK", "COUNT"]))
def test_action_type_valid_values(action_type):
    # Property: Action Type must be one of the valid WAF actions
    action = waf.Action(Type=action_type)
    assert action.Type == action_type


# Test 11: Multiple Rules with unique priorities
@given(
    rule_ids=st.lists(st.text(min_size=1), min_size=1, max_size=5, unique=True),
    priorities=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=5, unique=True)
)
def test_rules_priority_property(rule_ids, priorities):
    assume(len(rule_ids) == len(priorities))
    
    rules = []
    for rule_id, priority in zip(rule_ids, priorities):
        rule = waf.Rules(
            Action=waf.Action(Type="ALLOW"),
            Priority=priority,
            RuleId=rule_id
        )
        rules.append(rule)
        
        # Property: Each rule should preserve its priority and ID
        assert rule.Priority == priority
        assert rule.RuleId == rule_id