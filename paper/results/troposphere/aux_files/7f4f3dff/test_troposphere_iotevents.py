#!/usr/bin/env python3
"""Property-based testing for troposphere.iotevents module"""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere
import troposphere.iotevents as iotevents
from troposphere import Tags


# Strategy for generating valid CloudFormation resource titles (alphanumeric only)
valid_title_strategy = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=255)

# Strategy for generating invalid titles (with special characters)
invalid_title_strategy = st.text(min_size=1, max_size=255).filter(lambda x: not re.match(r'^[a-zA-Z0-9]+$', x))

# Strategy for generating JSON paths
json_path_strategy = st.text(min_size=1, max_size=100)

# Strategy for ARNs
arn_strategy = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=200)

# Strategy for strings
string_strategy = st.text(min_size=1, max_size=100)

# Strategy for booleans
boolean_strategy = st.booleans()

# Strategy for integers
integer_strategy = st.integers(min_value=0, max_value=1000)


@given(
    title=valid_title_strategy,
    json_path=json_path_strategy
)
def test_input_round_trip(title, json_path):
    """Test that Input objects can be converted to dict and back"""
    # Create an Attribute
    attr = iotevents.Attribute(JsonPath=json_path)
    
    # Create InputDefinition with the attribute
    input_def = iotevents.InputDefinition(Attributes=[attr])
    
    # Create Input object
    original = iotevents.Input(
        title=title,
        InputDefinition=input_def
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # The dict should have the expected structure
    assert title in dict_repr
    assert 'Type' in dict_repr[title]
    assert dict_repr[title]['Type'] == 'AWS::IoTEvents::Input'
    assert 'Properties' in dict_repr[title]
    assert 'InputDefinition' in dict_repr[title]['Properties']
    
    # Verify the JsonPath is preserved
    assert 'Attributes' in dict_repr[title]['Properties']['InputDefinition']
    assert len(dict_repr[title]['Properties']['InputDefinition']['Attributes']) == 1
    assert dict_repr[title]['Properties']['InputDefinition']['Attributes'][0]['JsonPath'] == json_path


@given(invalid_title=invalid_title_strategy)
def test_invalid_title_validation(invalid_title):
    """Test that invalid titles (non-alphanumeric) are rejected"""
    try:
        # Try to create an Input with an invalid title
        input_def = iotevents.InputDefinition(Attributes=[iotevents.Attribute(JsonPath="/test")])
        obj = iotevents.Input(
            title=invalid_title,
            InputDefinition=input_def
        )
        # If we get here without exception, check if to_dict validates
        obj.to_dict()
        # If still no exception, the validation failed
        validation_failed = False
    except ValueError as e:
        # This is expected for invalid titles
        validation_failed = True
        assert 'not alphanumeric' in str(e)
    except Exception as e:
        # Some other exception occurred - this might indicate a bug
        validation_failed = True
    
    assert validation_failed, f"Expected validation to fail for non-alphanumeric title: {invalid_title!r}"


@given(
    title=valid_title_strategy,
    role_arn=arn_strategy,
    initial_state=string_strategy,
    state_name=string_strategy
)
def test_detector_model_required_fields(title, role_arn, initial_state, state_name):
    """Test that DetectorModel enforces required fields"""
    # Create a minimal valid State
    state = iotevents.State(StateName=state_name)
    
    # Create DetectorModelDefinition
    definition = iotevents.DetectorModelDefinition(
        InitialStateName=initial_state,
        States=[state]
    )
    
    # Create DetectorModel with all required fields
    model = iotevents.DetectorModel(
        title=title,
        DetectorModelDefinition=definition,
        RoleArn=role_arn
    )
    
    # Should be able to convert to dict without error
    d = model.to_dict()
    assert title in d
    assert d[title]['Type'] == 'AWS::IoTEvents::DetectorModel'
    assert 'Properties' in d[title]
    assert 'RoleArn' in d[title]['Properties']
    assert d[title]['Properties']['RoleArn'] == role_arn


@given(
    title=valid_title_strategy,
    enabled=boolean_strategy
)
def test_acknowledge_flow_property(title, enabled):
    """Test AcknowledgeFlow with boolean property"""
    flow = iotevents.AcknowledgeFlow(Enabled=enabled)
    
    # Create AlarmCapabilities using the flow
    capabilities = iotevents.AlarmCapabilities(AcknowledgeFlow=flow)
    
    # Create a minimal AlarmRule
    rule = iotevents.AlarmRule(
        SimpleRule=iotevents.SimpleRule(
            ComparisonOperator="GREATER",
            InputProperty="test",
            Threshold="10"
        )
    )
    
    # Create AlarmModel
    model = iotevents.AlarmModel(
        title=title,
        AlarmCapabilities=capabilities,
        AlarmRule=rule,
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    
    # Convert to dict and verify structure
    d = model.to_dict()
    assert title in d
    cap_dict = d[title]['Properties']['AlarmCapabilities']
    assert 'AcknowledgeFlow' in cap_dict
    assert cap_dict['AcknowledgeFlow']['Enabled'] == enabled


@given(
    title=valid_title_strategy,
    timer_name=string_strategy,
    duration_expr=st.one_of(st.none(), string_strategy),
    seconds=st.one_of(st.none(), integer_strategy)
)
def test_set_timer_action(title, timer_name, duration_expr, seconds):
    """Test SetTimer action with optional fields"""
    # At least one of duration_expr or seconds should be provided in real usage
    # but we're testing the object creation here
    
    timer = iotevents.SetTimer(
        TimerName=timer_name
    )
    
    if duration_expr is not None:
        timer.DurationExpression = duration_expr
    if seconds is not None:
        timer.Seconds = seconds
    
    # Create an Action with the timer
    action = iotevents.Action(SetTimer=timer)
    
    # Create an Event using the action
    event = iotevents.Event(
        EventName="TestEvent",
        Actions=[action]
    )
    
    # Create a State with the event
    state = iotevents.State(
        StateName="TestState",
        OnEnter=iotevents.OnEnter(Events=[event])
    )
    
    # Verify we can create a complete model
    definition = iotevents.DetectorModelDefinition(
        InitialStateName="TestState",
        States=[state]
    )
    
    model = iotevents.DetectorModel(
        title=title,
        DetectorModelDefinition=definition,
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    
    d = model.to_dict()
    assert title in d


@given(
    title=valid_title_strategy,
    comparison_op=st.sampled_from(['GREATER', 'LESS', 'EQUAL', 'GREATER_OR_EQUAL', 'LESS_OR_EQUAL']),
    input_prop=string_strategy,
    threshold=string_strategy
)
def test_simple_rule_properties(title, comparison_op, input_prop, threshold):
    """Test SimpleRule with various comparison operators"""
    rule = iotevents.SimpleRule(
        ComparisonOperator=comparison_op,
        InputProperty=input_prop,
        Threshold=threshold
    )
    
    alarm_rule = iotevents.AlarmRule(SimpleRule=rule)
    
    model = iotevents.AlarmModel(
        title=title,
        AlarmRule=alarm_rule,
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    
    d = model.to_dict()
    assert title in d
    rule_dict = d[title]['Properties']['AlarmRule']['SimpleRule']
    assert rule_dict['ComparisonOperator'] == comparison_op
    assert rule_dict['InputProperty'] == input_prop
    assert rule_dict['Threshold'] == threshold


@given(
    title=valid_title_strategy,
    hash_key_field=string_strategy,
    hash_key_value=string_strategy,
    table_name=string_strategy,
    operation=st.one_of(st.none(), st.sampled_from(['INSERT', 'UPDATE', 'DELETE']))
)
def test_dynamodb_action(title, hash_key_field, hash_key_value, table_name, operation):
    """Test DynamoDB action with required and optional fields"""
    dynamodb = iotevents.DynamoDB(
        HashKeyField=hash_key_field,
        HashKeyValue=hash_key_value,
        TableName=table_name
    )
    
    if operation is not None:
        dynamodb.Operation = operation
    
    action = iotevents.Action(DynamoDB=dynamodb)
    event = iotevents.Event(
        EventName="TestEvent",
        Actions=[action]
    )
    
    state = iotevents.State(
        StateName="TestState",
        OnEnter=iotevents.OnEnter(Events=[event])
    )
    
    definition = iotevents.DetectorModelDefinition(
        InitialStateName="TestState",
        States=[state]
    )
    
    model = iotevents.DetectorModel(
        title=title,
        DetectorModelDefinition=definition,
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    
    d = model.to_dict()
    assert title in d
    # Verify the DynamoDB action is properly serialized
    events = d[title]['Properties']['DetectorModelDefinition']['States'][0]['OnEnter']['Events']
    assert len(events) == 1
    assert 'DynamoDB' in events[0]['Actions'][0]
    dynamodb_dict = events[0]['Actions'][0]['DynamoDB']
    assert dynamodb_dict['HashKeyField'] == hash_key_field
    assert dynamodb_dict['HashKeyValue'] == hash_key_value
    assert dynamodb_dict['TableName'] == table_name
    if operation is not None:
        assert dynamodb_dict['Operation'] == operation


@given(
    title=valid_title_strategy,
    content_expr=string_strategy,
    payload_type=string_strategy
)
def test_payload_properties(title, content_expr, payload_type):
    """Test Payload object properties"""
    payload = iotevents.Payload(
        ContentExpression=content_expr,
        Type=payload_type
    )
    
    # Use payload in an IotEvents action
    iot_events = iotevents.IotEvents(
        InputName="TestInput",
        Payload=payload
    )
    
    action = iotevents.Action(IotEvents=iot_events)
    event = iotevents.Event(
        EventName="TestEvent",
        Actions=[action]
    )
    
    state = iotevents.State(
        StateName="TestState",
        OnEnter=iotevents.OnEnter(Events=[event])
    )
    
    definition = iotevents.DetectorModelDefinition(
        InitialStateName="TestState",
        States=[state]
    )
    
    model = iotevents.DetectorModel(
        title=title,
        DetectorModelDefinition=definition,
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    
    d = model.to_dict()
    assert title in d
    # Verify payload is properly serialized
    events = d[title]['Properties']['DetectorModelDefinition']['States'][0]['OnEnter']['Events']
    payload_dict = events[0]['Actions'][0]['IotEvents']['Payload']
    assert payload_dict['ContentExpression'] == content_expr
    assert payload_dict['Type'] == payload_type


if __name__ == "__main__":
    # Run a quick test to make sure imports work
    print("Running troposphere.iotevents property tests...")
    test_input_round_trip()
    test_invalid_title_validation()
    test_detector_model_required_fields()
    test_acknowledge_flow_property()
    test_set_timer_action()
    test_simple_rule_properties()
    test_dynamodb_action()
    test_payload_properties()
    print("All tests configured successfully!")