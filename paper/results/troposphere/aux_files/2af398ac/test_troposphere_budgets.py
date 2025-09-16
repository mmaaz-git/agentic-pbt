import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.budgets as budgets
from troposphere.validators import boolean, integer, double


@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_valid_inputs(value):
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.floats(min_value=2),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    try:
        boolean(value)
        assert False, f"Expected ValueError for {value}"
    except ValueError:
        pass


@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.isdigit() or (x.startswith('-') and x[1:].isdigit())),
    st.sampled_from([0, 1, -1, "0", "1", "-1"])
))
def test_integer_validator_valid_inputs(value):
    result = integer(value)
    assert result == value
    int(result)


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: 
        x.replace('.', '', 1).replace('-', '', 1).replace('+', '', 1).replace('e', '', 1).replace('E', '', 1).isdigit()
        if x else False
    )
))
def test_double_validator_valid_inputs(value):
    try:
        float(str(value))
        is_valid = True
    except:
        is_valid = False
    
    if is_valid:
        result = double(value)
        assert result == value
        float(result)


@given(st.dictionaries(
    st.sampled_from(["IncludeCredit", "IncludeDiscount", "IncludeOtherSubscription", 
                     "IncludeRecurring", "IncludeRefund", "IncludeSubscription",
                     "IncludeSupport", "IncludeTax", "IncludeUpfront", 
                     "UseAmortized", "UseBlended"]),
    st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"])
))
def test_cost_types_boolean_properties(props):
    ct = budgets.CostTypes(**props)
    for key, value in props.items():
        stored_value = ct.properties.get(key)
        expected = boolean(value)
        assert stored_value == expected


@given(
    amount=st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    unit=st.text(min_size=1, max_size=10)
)
def test_spend_object_creation(amount, unit):
    spend = budgets.Spend(Amount=amount, Unit=unit)
    assert spend.properties["Amount"] == amount
    assert spend.properties["Unit"] == unit
    
    spend_dict = spend.to_dict()
    assert "Amount" in spend_dict
    assert "Unit" in spend_dict
    assert spend_dict["Amount"] == amount
    assert spend_dict["Unit"] == unit


@given(
    threshold=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    comparison_operator=st.sampled_from(["GREATER_THAN", "LESS_THAN", "EQUAL_TO"]),
    notification_type=st.sampled_from(["ACTUAL", "FORECASTED"])
)
def test_notification_creation_and_round_trip(threshold, comparison_operator, notification_type):
    notification = budgets.Notification(
        Threshold=threshold,
        ComparisonOperator=comparison_operator,
        NotificationType=notification_type
    )
    
    assert notification.properties["Threshold"] == threshold
    assert notification.properties["ComparisonOperator"] == comparison_operator
    assert notification.properties["NotificationType"] == notification_type
    
    notification_dict = notification.to_dict()
    assert notification_dict["Threshold"] == threshold
    assert notification_dict["ComparisonOperator"] == comparison_operator
    assert notification_dict["NotificationType"] == notification_type


@given(
    address=st.text(min_size=1, max_size=100),
    subscription_type=st.sampled_from(["EMAIL", "SNS"])
)
def test_subscriber_creation(address, subscription_type):
    subscriber = budgets.Subscriber(
        Address=address,
        SubscriptionType=subscription_type
    )
    
    assert subscriber.properties["Address"] == address
    assert subscriber.properties["SubscriptionType"] == subscription_type
    
    subscriber_dict = subscriber.to_dict()
    assert subscriber_dict["Address"] == address
    assert subscriber_dict["SubscriptionType"] == subscription_type


@given(
    key=st.text(min_size=1, max_size=50),
    value=st.text(min_size=0, max_size=100)
)
def test_resource_tag_creation(key, value):
    tag = budgets.ResourceTag(Key=key, Value=value)
    assert tag.properties["Key"] == key
    assert tag.properties["Value"] == value
    
    tag_dict = tag.to_dict()
    assert tag_dict["Key"] == key
    assert tag_dict["Value"] == value


@given(
    budget_adjustment_period=st.integers(min_value=1, max_value=60)
)
def test_historical_options_integer_validation(budget_adjustment_period):
    ho = budgets.HistoricalOptions(BudgetAdjustmentPeriod=budget_adjustment_period)
    assert ho.properties["BudgetAdjustmentPeriod"] == budget_adjustment_period


@given(
    policy_id=st.text(min_size=1, max_size=100),
    target_ids=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10)
)
def test_scp_action_definition(policy_id, target_ids):
    scp = budgets.ScpActionDefinition(
        PolicyId=policy_id,
        TargetIds=target_ids
    )
    assert scp.properties["PolicyId"] == policy_id
    assert scp.properties["TargetIds"] == target_ids
    
    scp_dict = scp.to_dict()
    assert scp_dict["PolicyId"] == policy_id
    assert scp_dict["TargetIds"] == target_ids


@given(
    instance_ids=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
    region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
    subtype=st.sampled_from(["STOP_EC2_INSTANCES", "STOP_RDS_INSTANCES"])
)
def test_ssm_action_definition(instance_ids, region, subtype):
    ssm = budgets.SsmActionDefinition(
        InstanceIds=instance_ids,
        Region=region,
        Subtype=subtype
    )
    assert ssm.properties["InstanceIds"] == instance_ids
    assert ssm.properties["Region"] == region
    assert ssm.properties["Subtype"] == subtype


@given(
    threshold_type=st.sampled_from(["PERCENTAGE", "ABSOLUTE_VALUE"]),
    threshold_value=st.floats(min_value=0, max_value=1000, allow_nan=False)
)
def test_action_threshold_double_validation(threshold_type, threshold_value):
    at = budgets.ActionThreshold(
        Type=threshold_type,
        Value=threshold_value
    )
    assert at.properties["Type"] == threshold_type
    assert at.properties["Value"] == threshold_value