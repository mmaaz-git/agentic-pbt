import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.route53recoverycontrol as r53rc
from troposphere.validators import boolean, integer

# Test 1: Boolean validator round-trip property
@given(st.sampled_from([True, False, 1, 0, "true", "True", "false", "False", "1", "0"]))
def test_boolean_validator_idempotent(value):
    """Boolean validator should be idempotent - applying it twice should give same result"""
    result1 = boolean(value)
    result2 = boolean(result1)
    assert result1 == result2
    assert isinstance(result1, bool)
    assert isinstance(result2, bool)

@given(st.one_of(
    st.booleans(),
    st.sampled_from([0, 1]),
    st.sampled_from(["true", "True", "false", "False", "0", "1"])
))
def test_boolean_validator_always_returns_bool(value):
    """Boolean validator should always return a bool for valid inputs"""
    result = boolean(value)
    assert isinstance(result, bool)

# Test 2: Integer validator properties
@given(st.integers())
def test_integer_validator_accepts_integers(value):
    """Integer validator should accept all integers"""
    result = integer(value)
    assert int(result) == value

@given(st.text())
def test_integer_validator_string_round_trip(value):
    """Integer validator should only accept strings that can be parsed as integers"""
    try:
        int(value)
        can_parse = True
    except (ValueError, TypeError):
        can_parse = False
    
    if can_parse:
        result = integer(value)
        assert int(result) == int(value)
    else:
        try:
            integer(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError:
            pass  # Expected

@given(st.floats())
def test_integer_validator_with_floats(value):
    """Integer validator behavior with floats - should accept if convertible to int"""
    if math.isnan(value) or math.isinf(value):
        try:
            integer(value)
            assert False, f"Should have raised error for {value}"
        except (ValueError, OverflowError):
            pass  # Expected
    elif value == int(value):  # Float is actually an integer
        result = integer(value)
        assert int(result) == int(value)
    else:
        # Non-integer floats should work if they can be converted
        result = integer(value)
        assert int(result) == int(value)

# Test 3: Class instantiation properties
@given(st.text(min_size=1).filter(lambda x: x.isalnum()))
def test_cluster_instantiation(name):
    """Cluster class should instantiate with valid required parameters"""
    cluster = r53rc.Cluster(title="TestCluster", Name=name)
    assert cluster.Name == name
    assert cluster.title == "TestCluster"

@given(st.text(min_size=1).filter(lambda x: x.isalnum()))
def test_control_panel_instantiation(name):
    """ControlPanel class should instantiate with valid required parameters"""
    panel = r53rc.ControlPanel(title="TestPanel", Name=name)
    assert panel.Name == name
    assert panel.title == "TestPanel"

@given(st.text(min_size=1).filter(lambda x: x.isalnum()))
def test_routing_control_instantiation(name):
    """RoutingControl class should instantiate with valid required parameters"""
    control = r53rc.RoutingControl(title="TestControl", Name=name)
    assert control.Name == name
    assert control.title == "TestControl"

@given(
    st.lists(st.text(min_size=1), min_size=1),
    st.integers(min_value=0, max_value=2147483647)
)
def test_assertion_rule_instantiation(controls, wait_period):
    """AssertionRule property should instantiate with valid required parameters"""
    rule = r53rc.AssertionRule(
        AssertedControls=controls,
        WaitPeriodMs=wait_period
    )
    assert rule.AssertedControls == controls
    assert rule.WaitPeriodMs == wait_period

@given(
    st.lists(st.text(min_size=1), min_size=1),
    st.lists(st.text(min_size=1), min_size=1),
    st.integers(min_value=0, max_value=2147483647)
)
def test_gating_rule_instantiation(gating_controls, target_controls, wait_period):
    """GatingRule property should instantiate with valid required parameters"""
    rule = r53rc.GatingRule(
        GatingControls=gating_controls,
        TargetControls=target_controls,
        WaitPeriodMs=wait_period
    )
    assert rule.GatingControls == gating_controls
    assert rule.TargetControls == target_controls
    assert rule.WaitPeriodMs == wait_period

@given(
    st.booleans(),
    st.integers(min_value=0, max_value=100),
    st.sampled_from(["ATLEAST", "AND", "OR"])
)
def test_rule_config_instantiation(inverted, threshold, rule_type):
    """RuleConfig property should instantiate with valid required parameters"""
    config = r53rc.RuleConfig(
        Inverted=inverted,
        Threshold=threshold,
        Type=rule_type
    )
    # Test that boolean validator is applied
    assert config.Inverted in [True, False]
    assert config.Threshold == threshold
    assert config.Type == rule_type

@given(
    st.text(min_size=1).filter(lambda x: x.isalnum()),
    st.text(min_size=1),
    st.booleans(),
    st.integers(min_value=0, max_value=100),
    st.sampled_from(["ATLEAST", "AND", "OR"])
)
def test_safety_rule_instantiation(name, panel_arn, inverted, threshold, rule_type):
    """SafetyRule class should instantiate with valid required parameters"""
    rule_config = r53rc.RuleConfig(
        Inverted=inverted,
        Threshold=threshold,
        Type=rule_type
    )
    safety_rule = r53rc.SafetyRule(
        title="TestSafetyRule",
        Name=name,
        ControlPanelArn=panel_arn,
        RuleConfig=rule_config
    )
    assert safety_rule.Name == name
    assert safety_rule.ControlPanelArn == panel_arn
    assert safety_rule.RuleConfig == rule_config

# Test property validation with invalid types
@given(st.text(min_size=1).filter(lambda x: x.isalnum()))
def test_wait_period_requires_integer_validation(name):
    """WaitPeriodMs should require integer validation"""
    # This should work with an integer
    rule1 = r53rc.AssertionRule(
        AssertedControls=["control1"],
        WaitPeriodMs=1000
    )
    assert rule1.WaitPeriodMs == 1000
    
    # This should also work with a string that can be converted to int
    rule2 = r53rc.AssertionRule(
        AssertedControls=["control2"],
        WaitPeriodMs="2000"
    )
    assert int(rule2.WaitPeriodMs) == 2000
    
    # This should fail with non-integer string
    try:
        rule3 = r53rc.AssertionRule(
            AssertedControls=["control3"],
            WaitPeriodMs="not_a_number"
        )
        assert False, "Should have raised ValueError for non-integer string"
    except (ValueError, TypeError):
        pass  # Expected

@given(st.one_of(
    st.none(),
    st.floats(),
    st.text(),
    st.lists(st.integers())
))
def test_inverted_requires_boolean_validation(value):
    """Inverted property should use boolean validation"""
    valid_bool_values = [True, False, 0, 1, "true", "True", "false", "False", "0", "1"]
    
    if value in valid_bool_values:
        config = r53rc.RuleConfig(
            Inverted=value,
            Threshold=50,
            Type="AND"
        )
        assert config.Inverted in [True, False]
    else:
        try:
            config = r53rc.RuleConfig(
                Inverted=value,
                Threshold=50,
                Type="AND"
            )
            # If we get here, check if it was converted to boolean
            if hasattr(config, 'Inverted'):
                assert config.Inverted in [True, False], f"Unexpected value: {config.Inverted}"
        except (ValueError, TypeError, AttributeError):
            pass  # Expected for invalid values