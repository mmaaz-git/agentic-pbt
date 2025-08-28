import json
import pytest
from hypothesis import given, strategies as st, assume, settings
from troposphere import validators
from troposphere.s3objectlambda import (
    AccessPoint,
    AccessPointPolicy,
    Alias,
    AwsLambda,
    ContentTransformation,
    ObjectLambdaConfiguration,
    PublicAccessBlockConfiguration,
    TransformationConfiguration,
)


# Test 1: Boolean validator property
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(min_size=1),
    st.integers(),
    st.floats(allow_nan=False),
    st.none(),
    st.dictionaries(st.text(), st.text()),
    st.lists(st.integers())
))
def test_boolean_validator_consistency(value):
    """Test that boolean validator accepts documented values and rejects others"""
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    if value in true_values:
        assert validators.boolean(value) is True
    elif value in false_values:
        assert validators.boolean(value) is False
    else:
        with pytest.raises(ValueError):
            validators.boolean(value)


# Test 2: Required properties validation
@given(
    function_arn=st.text(min_size=1),
    function_payload=st.one_of(st.none(), st.text()),
    include_required=st.booleans()
)
def test_awslambda_required_properties(function_arn, function_payload, include_required):
    """Test that AwsLambda enforces required FunctionArn property"""
    kwargs = {}
    if include_required:
        kwargs['FunctionArn'] = function_arn
    if function_payload is not None:
        kwargs['FunctionPayload'] = function_payload
    
    if include_required:
        # Should succeed with required property
        obj = AwsLambda(**kwargs)
        assert obj.properties.get('FunctionArn') == function_arn
    else:
        # Should fail without required property
        with pytest.raises(ValueError) as exc_info:
            obj = AwsLambda(**kwargs)
            obj.to_dict()  # Validation happens during to_dict
        assert "FunctionArn" in str(exc_info.value)
        assert "required" in str(exc_info.value)


# Test 3: to_dict/to_json round-trip property
@given(
    status=st.one_of(st.none(), st.text(min_size=1)),
    value=st.text(min_size=1)
)
def test_alias_to_dict_to_json_consistency(status, value):
    """Test that to_dict and to_json are consistent for Alias objects"""
    kwargs = {'Value': value}
    if status is not None:
        kwargs['Status'] = status
    
    alias = Alias(**kwargs)
    
    # Get dict and JSON representations
    dict_repr = alias.to_dict()
    json_repr = alias.to_json(indent=0, sort_keys=True)
    
    # JSON should be parseable and match the dict
    parsed_json = json.loads(json_repr)
    assert parsed_json == dict_repr
    
    # The dict should contain the properties we set
    assert dict_repr['Value'] == value
    if status is not None:
        assert dict_repr['Status'] == status


# Test 4: Object equality property
@given(
    block_acls=st.booleans(),
    block_policy=st.booleans(),
    ignore_acls=st.booleans(),
    restrict_buckets=st.booleans()
)
def test_publicaccessblock_equality_property(block_acls, block_policy, ignore_acls, restrict_buckets):
    """Test that two PublicAccessBlockConfiguration objects with same properties are equal"""
    kwargs = {}
    if block_acls:
        kwargs['BlockPublicAcls'] = True
    if block_policy:
        kwargs['BlockPublicPolicy'] = True
    if ignore_acls:
        kwargs['IgnorePublicAcls'] = True
    if restrict_buckets:
        kwargs['RestrictPublicBuckets'] = True
    
    obj1 = PublicAccessBlockConfiguration(**kwargs)
    obj2 = PublicAccessBlockConfiguration(**kwargs)
    
    # Same properties should mean equal objects
    assert obj1 == obj2
    assert obj1.to_dict() == obj2.to_dict()
    assert obj1.to_json(indent=0) == obj2.to_json(indent=0)


# Test 5: ContentTransformation nested property validation
@given(
    function_arn=st.text(min_size=1),
    function_payload=st.one_of(st.none(), st.text())
)
def test_content_transformation_nested_validation(function_arn, function_payload):
    """Test that ContentTransformation properly validates nested AwsLambda"""
    kwargs = {'FunctionArn': function_arn}
    if function_payload is not None:
        kwargs['FunctionPayload'] = function_payload
    
    aws_lambda = AwsLambda(**kwargs)
    content_transform = ContentTransformation(AwsLambda=aws_lambda)
    
    # Should be able to convert to dict
    result = content_transform.to_dict()
    assert 'AwsLambda' in result
    assert result['AwsLambda']['FunctionArn'] == function_arn
    
    
# Test 6: AccessPointPolicy validates required properties
@given(
    access_point=st.text(min_size=1),
    policy_doc=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.text(), st.integers(), st.lists(st.text()))
    )
)
def test_access_point_policy_required_properties(access_point, policy_doc):
    """Test that AccessPointPolicy enforces both required properties"""
    # Both properties are required
    policy = AccessPointPolicy(
        ObjectLambdaAccessPoint=access_point,
        PolicyDocument=policy_doc
    )
    
    result = policy.to_dict()
    assert result['Properties']['ObjectLambdaAccessPoint'] == access_point
    assert result['Properties']['PolicyDocument'] == policy_doc
    
    # Test missing required property
    with pytest.raises(ValueError) as exc_info:
        bad_policy = AccessPointPolicy(ObjectLambdaAccessPoint=access_point)
        bad_policy.to_dict()
    assert "PolicyDocument" in str(exc_info.value)
    assert "required" in str(exc_info.value)


# Test 7: TransformationConfiguration list property
@given(
    actions=st.lists(st.text(min_size=1), min_size=1, max_size=5),
    function_arn=st.text(min_size=1)
)
def test_transformation_configuration_actions_list(actions, function_arn):
    """Test that TransformationConfiguration properly handles Actions list"""
    aws_lambda = AwsLambda(FunctionArn=function_arn)
    content = ContentTransformation(AwsLambda=aws_lambda)
    
    transform = TransformationConfiguration(
        Actions=actions,
        ContentTransformation=content
    )
    
    result = transform.to_dict()
    assert result['Actions'] == actions
    assert len(result['Actions']) == len(actions)
    
    
# Test 8: AccessPoint name property is optional
@given(
    name=st.one_of(st.none(), st.text(min_size=1)),
    supporting_ap=st.text(min_size=1),
    function_arn=st.text(min_size=1),
    actions=st.lists(st.text(min_size=1), min_size=1, max_size=3)
)
def test_access_point_optional_name(name, supporting_ap, function_arn, actions):
    """Test that AccessPoint Name property is truly optional"""
    aws_lambda = AwsLambda(FunctionArn=function_arn)
    content = ContentTransformation(AwsLambda=aws_lambda)
    transform_config = TransformationConfiguration(
        Actions=actions,
        ContentTransformation=content
    )
    
    obj_lambda_config = ObjectLambdaConfiguration(
        SupportingAccessPoint=supporting_ap,
        TransformationConfigurations=[transform_config]
    )
    
    kwargs = {'ObjectLambdaConfiguration': obj_lambda_config}
    if name is not None:
        kwargs['Name'] = name
    
    # Should work with or without Name
    access_point = AccessPoint(**kwargs)
    result = access_point.to_dict()
    
    assert result['Type'] == 'AWS::S3ObjectLambda::AccessPoint'
    if name is not None:
        assert result['Properties']['Name'] == name
    else:
        assert 'Name' not in result['Properties']