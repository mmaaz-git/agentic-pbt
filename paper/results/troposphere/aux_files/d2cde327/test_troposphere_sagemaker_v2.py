"""Property-based tests for troposphere.sagemaker module - revised version."""

import json
from hypothesis import assume, given, strategies as st, settings
import troposphere.sagemaker as sm
import troposphere
import inspect


# Strategy for valid CloudFormation logical IDs (alphanumeric only)
cf_logical_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=63
)

# Strategy for AWS resource names (can include hyphens)
aws_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-"),
    min_size=1,
    max_size=63
).filter(lambda x: x[0].isalpha() and not x.endswith('-'))

# Strategy for ARNs
arn_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=":/-"),
    min_size=10,
    max_size=100
).map(lambda x: f"arn:aws:iam::123456789012:role/{x}")

# Strategy for VPC IDs
vpc_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
    min_size=4, 
    max_size=20
).map(lambda x: f"vpc-{x}")

# Strategy for subnet IDs
subnet_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
    min_size=4,
    max_size=20
).map(lambda x: f"subnet-{x}")


@given(
    title=cf_logical_id_strategy,
    domain_name=aws_name_strategy,
    vpc_id=vpc_id_strategy,
    subnet_ids=st.lists(subnet_id_strategy, min_size=1, max_size=5),
    auth_mode=st.sampled_from(['IAM', 'SSO'])
)
@settings(max_examples=100)
def test_domain_serialization_roundtrip(title, domain_name, vpc_id, subnet_ids, auth_mode):
    """Test Domain to_dict/from_dict round-trip preserves data."""
    domain = sm.Domain(title)
    domain.DomainName = domain_name
    domain.VpcId = vpc_id
    domain.SubnetIds = subnet_ids
    domain.AuthMode = auth_mode
    domain.DefaultUserSettings = sm.UserSettings()
    
    # Serialize to dict
    dict_repr = domain.to_dict()
    
    # The API inconsistency: to_dict returns full CloudFormation format,
    # but from_dict expects only Properties
    properties = dict_repr['Properties']
    new_domain = sm.Domain.from_dict(title + '2', properties)
    new_dict = new_domain.to_dict()
    
    # Properties should be preserved
    assert dict_repr['Properties'] == new_dict['Properties']
    

@given(
    title=cf_logical_id_strategy,
    model_name=aws_name_strategy,
    execution_role_arn=arn_strategy
)
@settings(max_examples=100)
def test_model_ref_method(title, model_name, execution_role_arn):
    """Test Model.Ref() and Model.ref() return expected CloudFormation reference."""
    model = sm.Model(title)
    model.ModelName = model_name
    model.ExecutionRoleArn = execution_role_arn
    
    # Both Ref() and ref() should return the same CloudFormation reference
    ref1 = model.Ref()
    ref2 = model.ref()
    
    assert ref1 == ref2
    assert ref1 == {'Ref': title}
    

@given(
    title=cf_logical_id_strategy,
    endpoint_name=aws_name_strategy,
    endpoint_config_name=aws_name_strategy
)
@settings(max_examples=100) 
def test_endpoint_get_att(title, endpoint_name, endpoint_config_name):
    """Test Endpoint.GetAtt() method for retrieving CloudFormation attributes."""
    endpoint = sm.Endpoint(title)
    endpoint.EndpointName = endpoint_name
    endpoint.EndpointConfigName = endpoint_config_name
    
    # GetAtt should return CloudFormation Fn::GetAtt reference
    endpoint_arn = endpoint.GetAtt('EndpointName')
    
    assert endpoint_arn == {'Fn::GetAtt': [title, 'EndpointName']}
    
    # get_att (lowercase) should also work
    endpoint_arn2 = endpoint.get_att('EndpointName')
    assert endpoint_arn == endpoint_arn2
    

@given(
    title=cf_logical_id_strategy,
    tags_dict=st.dictionaries(
        st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100)
def test_tags_constructor_dict(title, tags_dict):
    """Test that Tags can be constructed from a dict."""
    model = sm.Model(title)
    model.ExecutionRoleArn = 'arn:aws:iam::123456789012:role/TestRole'
    
    # Create Tags from dict
    tags = troposphere.Tags(tags_dict)
    model.Tags = tags
    
    # Serialize
    dict_repr = model.to_dict()
    
    # Check tags are serialized correctly
    if tags_dict:
        assert 'Tags' in dict_repr['Properties']
        serialized_tags = dict_repr['Properties']['Tags']
        
        # Tags should be list of {Key: k, Value: v} dicts
        assert len(serialized_tags) == len(tags_dict)
        
        # Check all keys are present
        tag_keys = {tag['Key'] for tag in serialized_tags}
        assert tag_keys == set(tags_dict.keys())
        

@given(
    title=cf_logical_id_strategy,
    notebook_name=aws_name_strategy,
    role_arn=arn_strategy,
    instance_type=st.sampled_from(['ml.t2.medium', 'ml.t3.medium', 'ml.m5.xlarge', 'ml.p3.2xlarge'])
)
@settings(max_examples=100)
def test_notebook_instance_json_roundtrip(title, notebook_name, role_arn, instance_type):
    """Test NotebookInstance JSON serialization round-trip."""
    notebook = sm.NotebookInstance(title)
    notebook.NotebookInstanceName = notebook_name
    notebook.RoleArn = role_arn
    notebook.InstanceType = instance_type
    
    # Serialize to JSON
    json_str = notebook.to_json()
    
    # Parse JSON
    parsed = json.loads(json_str)
    
    # Verify structure
    assert parsed['Type'] == 'AWS::SageMaker::NotebookInstance'
    assert parsed['Properties']['NotebookInstanceName'] == notebook_name
    assert parsed['Properties']['RoleArn'] == role_arn
    assert parsed['Properties']['InstanceType'] == instance_type
    
    # Create new instance from parsed properties
    new_notebook = sm.NotebookInstance.from_dict(title + '2', parsed['Properties'])
    
    # Verify round-trip
    assert new_notebook.NotebookInstanceName == notebook_name
    assert new_notebook.RoleArn == role_arn
    assert new_notebook.InstanceType == instance_type
    

@given(
    title=cf_logical_id_strategy,
    config_name=aws_name_strategy,
    production_variants=st.lists(
        st.fixed_dictionaries({
            'ModelName': aws_name_strategy,
            'VariantName': st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                min_size=1,
                max_size=63
            ),
            'InitialInstanceCount': st.integers(min_value=1, max_value=10),
            'InstanceType': st.sampled_from(['ml.t2.medium', 'ml.m5.xlarge'])
        }),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=50)
def test_endpoint_config_with_production_variants(title, config_name, production_variants):
    """Test EndpointConfig with ProductionVariant objects."""
    config = sm.EndpointConfig(title)
    config.EndpointConfigName = config_name
    
    # Create ProductionVariant objects
    variant_objects = []
    for pv_dict in production_variants:
        variant = sm.ProductionVariant()
        variant.ModelName = pv_dict['ModelName']
        variant.VariantName = pv_dict['VariantName']
        variant.InitialInstanceCount = pv_dict['InitialInstanceCount']
        variant.InstanceType = pv_dict['InstanceType']
        variant_objects.append(variant)
    
    config.ProductionVariants = variant_objects
    
    # Serialize
    dict_repr = config.to_dict()
    
    # Verify structure
    assert dict_repr['Type'] == 'AWS::SageMaker::EndpointConfig'
    assert 'ProductionVariants' in dict_repr['Properties']
    assert len(dict_repr['Properties']['ProductionVariants']) == len(production_variants)
    
    # Each variant should be serialized correctly
    for i, variant_dict in enumerate(dict_repr['Properties']['ProductionVariants']):
        assert variant_dict['ModelName'] == production_variants[i]['ModelName']
        assert variant_dict['VariantName'] == production_variants[i]['VariantName']
        

@given(
    title=cf_logical_id_strategy,
    image_uri=st.text(min_size=1, max_size=255).filter(lambda x: not x.startswith('s3://')),
    model_data_url=st.text(min_size=1, max_size=100).map(lambda x: f"s3://bucket/{x}"),
    environment_vars=st.dictionaries(
        st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
        st.text(min_size=0, max_size=200),
        min_size=0,
        max_size=5
    )
)
@settings(max_examples=100)
def test_container_definition_with_environment(title, image_uri, model_data_url, environment_vars):
    """Test ContainerDefinition with environment variables."""
    model = sm.Model(title)
    model.ExecutionRoleArn = 'arn:aws:iam::123456789012:role/TestRole'
    
    # Create container definition
    container = sm.ContainerDefinition()
    container.Image = image_uri
    container.ModelDataUrl = model_data_url
    container.Environment = environment_vars
    
    model.PrimaryContainer = container
    
    # Serialize
    dict_repr = model.to_dict()
    
    # Verify container is serialized
    assert 'PrimaryContainer' in dict_repr['Properties']
    pc = dict_repr['Properties']['PrimaryContainer']
    
    assert pc['Image'] == image_uri
    assert pc['ModelDataUrl'] == model_data_url
    
    if environment_vars:
        assert pc['Environment'] == environment_vars
        

@given(
    title=cf_logical_id_strategy,
    enable_capture=st.booleans(),
    initial_sampling_percentage=st.integers(min_value=0, max_value=100),
    destination_s3_uri=st.text(min_size=1, max_size=100).map(lambda x: f"s3://bucket/{x}"),
    kms_key_id=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-"),
                       min_size=1, max_size=100)
)
@settings(max_examples=100)
def test_data_capture_config(title, enable_capture, initial_sampling_percentage, 
                             destination_s3_uri, kms_key_id):
    """Test DataCaptureConfig properties."""
    config = sm.EndpointConfig(title)
    config.EndpointConfigName = f"config-{title}"
    
    # Create minimal production variant
    variant = sm.ProductionVariant()
    variant.ModelName = 'test-model'
    variant.VariantName = 'AllTraffic'
    variant.InitialInstanceCount = 1
    variant.InstanceType = 'ml.t2.medium'
    config.ProductionVariants = [variant]
    
    # Create DataCaptureConfig
    capture_config = sm.DataCaptureConfig()
    capture_config.EnableCapture = enable_capture
    capture_config.InitialSamplingPercentage = initial_sampling_percentage
    capture_config.DestinationS3Uri = destination_s3_uri
    capture_config.KmsKeyId = kms_key_id
    
    # Create CaptureOptions
    capture_option = sm.CaptureOption()
    capture_option.CaptureMode = 'Input'
    capture_config.CaptureOptions = [capture_option]
    
    config.DataCaptureConfig = capture_config
    
    # Serialize
    dict_repr = config.to_dict()
    
    # Verify DataCaptureConfig is serialized
    assert 'DataCaptureConfig' in dict_repr['Properties']
    dcc = dict_repr['Properties']['DataCaptureConfig']
    
    assert dcc['EnableCapture'] == enable_capture
    assert dcc['InitialSamplingPercentage'] == initial_sampling_percentage
    assert dcc['DestinationS3Uri'] == destination_s3_uri
    assert dcc['KmsKeyId'] == kms_key_id
    assert len(dcc['CaptureOptions']) == 1
    assert dcc['CaptureOptions'][0]['CaptureMode'] == 'Input'