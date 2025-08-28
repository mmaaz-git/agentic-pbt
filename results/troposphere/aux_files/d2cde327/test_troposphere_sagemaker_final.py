"""Property-based tests for troposphere.sagemaker module - final version."""

import json
from hypothesis import given, strategies as st, settings
import troposphere.sagemaker as sm
import troposphere


# ASCII-only alphanumeric for CloudFormation logical IDs
ASCII_ALPHANUMERIC = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

cf_logical_id_strategy = st.text(
    alphabet=ASCII_ALPHANUMERIC,
    min_size=1,
    max_size=63
)

# AWS names can include hyphens
aws_name_strategy = st.text(
    alphabet=ASCII_ALPHANUMERIC + '-',
    min_size=1,
    max_size=63
).filter(lambda x: x[0].isalpha() and not x.endswith('-'))

# ARN strategy
arn_strategy = st.text(
    alphabet=ASCII_ALPHANUMERIC + ':/-',
    min_size=10,
    max_size=100
).map(lambda x: f"arn:aws:iam::123456789012:role/{x}")


@given(
    title=cf_logical_id_strategy,
    model_name=aws_name_strategy,
    execution_role_arn=arn_strategy
)
@settings(max_examples=100)
def test_model_ref_returns_ref_object(title, model_name, execution_role_arn):
    """Test that Model.ref() returns a Ref object with correct CloudFormation reference."""
    model = sm.Model(title)
    model.ModelName = model_name
    model.ExecutionRoleArn = execution_role_arn
    
    # ref() returns a Ref object
    ref_obj = model.ref()
    assert isinstance(ref_obj, troposphere.Ref)
    
    # When converted to dict, it should be a CloudFormation Ref
    ref_dict = ref_obj.to_dict()
    assert ref_dict == {'Ref': title}
    
    # Ref() should return the same type of object
    Ref_obj = model.Ref()
    assert isinstance(Ref_obj, troposphere.Ref)
    assert Ref_obj.to_dict() == ref_dict


@given(
    title=cf_logical_id_strategy,
    domain_name=aws_name_strategy,
    vpc_id=st.text(alphabet=ASCII_ALPHANUMERIC, min_size=4, max_size=20).map(lambda x: f"vpc-{x}"),
    subnet_ids=st.lists(
        st.text(alphabet=ASCII_ALPHANUMERIC, min_size=4, max_size=20).map(lambda x: f"subnet-{x}"),
        min_size=1,
        max_size=5
    ),
    auth_mode=st.sampled_from(['IAM', 'SSO'])
)
@settings(max_examples=100)
def test_domain_to_dict_from_dict_inconsistency(title, domain_name, vpc_id, subnet_ids, auth_mode):
    """
    Test demonstrates the API inconsistency: to_dict() returns full CloudFormation
    format but from_dict() expects only Properties portion.
    """
    domain = sm.Domain(title)
    domain.DomainName = domain_name
    domain.VpcId = vpc_id
    domain.SubnetIds = subnet_ids
    domain.AuthMode = auth_mode
    domain.DefaultUserSettings = sm.UserSettings()
    
    # to_dict returns full CloudFormation resource format
    dict_repr = domain.to_dict()
    assert 'Type' in dict_repr
    assert 'Properties' in dict_repr
    assert dict_repr['Type'] == 'AWS::SageMaker::Domain'
    
    # from_dict expects only the Properties, not the full format
    # This would fail: sm.Domain.from_dict('New', dict_repr)
    # This works:
    new_domain = sm.Domain.from_dict(title + '2', dict_repr['Properties'])
    
    # Verify round-trip preserves properties
    new_dict = new_domain.to_dict()
    assert dict_repr['Properties'] == new_dict['Properties']


@given(
    title=cf_logical_id_strategy,
    tags_dict=st.dictionaries(
        st.text(alphabet=ASCII_ALPHANUMERIC, min_size=1, max_size=50),
        st.text(min_size=0, max_size=100),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100)
def test_tags_serialization(title, tags_dict):
    """Test Tags object serialization to CloudFormation format."""
    model = sm.Model(title)
    model.ExecutionRoleArn = 'arn:aws:iam::123456789012:role/TestRole'
    
    # Create Tags from dict
    tags = troposphere.Tags(tags_dict)
    model.Tags = tags
    
    # Serialize
    dict_repr = model.to_dict()
    
    # Tags should be serialized as list of Key/Value pairs
    assert 'Tags' in dict_repr['Properties']
    serialized_tags = dict_repr['Properties']['Tags']
    
    # Should be list of dicts with Key and Value
    assert isinstance(serialized_tags, list)
    assert len(serialized_tags) == len(tags_dict)
    
    # Check all tags are present
    tag_map = {tag['Key']: tag['Value'] for tag in serialized_tags}
    assert tag_map == tags_dict


@given(
    title=cf_logical_id_strategy,
    endpoint_name=aws_name_strategy,
    endpoint_config_name=aws_name_strategy,
    attribute_name=st.sampled_from(['EndpointName', 'EndpointArn'])
)
@settings(max_examples=100)
def test_endpoint_get_att_returns_getatt_object(title, endpoint_name, endpoint_config_name, attribute_name):
    """Test that GetAtt returns proper CloudFormation GetAtt reference."""
    endpoint = sm.Endpoint(title)
    endpoint.EndpointName = endpoint_name
    endpoint.EndpointConfigName = endpoint_config_name
    
    # GetAtt should return a GetAtt object
    getatt_obj = endpoint.GetAtt(attribute_name)
    assert isinstance(getatt_obj, troposphere.GetAtt)
    
    # When converted to dict, should be CloudFormation Fn::GetAtt
    getatt_dict = getatt_obj.to_dict()
    assert getatt_dict == {'Fn::GetAtt': [title, attribute_name]}
    
    # get_att (lowercase) should work the same
    getatt_obj2 = endpoint.get_att(attribute_name)
    assert isinstance(getatt_obj2, troposphere.GetAtt)
    assert getatt_obj2.to_dict() == getatt_dict


@given(
    title=cf_logical_id_strategy,
    containers=st.lists(
        st.fixed_dictionaries({
            'Image': st.text(min_size=1, max_size=255),
            'ModelDataUrl': st.text(min_size=1, max_size=100).map(lambda x: f"s3://bucket/{x}"),
            'ContainerHostname': st.text(alphabet=ASCII_ALPHANUMERIC + '-', min_size=1, max_size=63)
        }),
        min_size=1,
        max_size=5
    ),
    execution_role_arn=arn_strategy
)
@settings(max_examples=50)
def test_model_with_multiple_containers(title, containers, execution_role_arn):
    """Test Model with multiple container definitions."""
    model = sm.Model(title)
    model.ExecutionRoleArn = execution_role_arn
    
    # Create ContainerDefinition objects
    container_objects = []
    for c_dict in containers:
        container = sm.ContainerDefinition()
        container.Image = c_dict['Image']
        container.ModelDataUrl = c_dict['ModelDataUrl']
        container.ContainerHostname = c_dict['ContainerHostname']
        container_objects.append(container)
    
    model.Containers = container_objects
    
    # Serialize
    dict_repr = model.to_dict()
    
    # Verify containers are serialized
    assert 'Containers' in dict_repr['Properties']
    assert len(dict_repr['Properties']['Containers']) == len(containers)
    
    # Each container should be serialized correctly
    for i, container_dict in enumerate(dict_repr['Properties']['Containers']):
        assert container_dict['Image'] == containers[i]['Image']
        assert container_dict['ModelDataUrl'] == containers[i]['ModelDataUrl']
        assert container_dict['ContainerHostname'] == containers[i]['ContainerHostname']


@given(
    title=cf_logical_id_strategy,
    notebook_name=aws_name_strategy,
    role_arn=arn_strategy,
    instance_type=st.sampled_from(['ml.t2.medium', 'ml.t3.medium', 'ml.m5.xlarge']),
    volume_size_gb=st.integers(min_value=5, max_value=16384)
)
@settings(max_examples=100)
def test_notebook_instance_validation(title, notebook_name, role_arn, instance_type, volume_size_gb):
    """Test NotebookInstance validation passes for valid inputs."""
    notebook = sm.NotebookInstance(title)
    notebook.NotebookInstanceName = notebook_name
    notebook.RoleArn = role_arn
    notebook.InstanceType = instance_type
    notebook.VolumeSizeInGB = volume_size_gb
    
    # Should validate without errors
    errors = notebook.validate()
    assert errors == []
    
    # Should serialize successfully
    dict_repr = notebook.to_dict()
    assert dict_repr['Type'] == 'AWS::SageMaker::NotebookInstance'
    assert dict_repr['Properties']['NotebookInstanceName'] == notebook_name
    assert dict_repr['Properties']['VolumeSizeInGB'] == volume_size_gb


@given(
    title=cf_logical_id_strategy,
    project_name=aws_name_strategy,
    product_id=st.text(alphabet=ASCII_ALPHANUMERIC + '-', min_size=1, max_size=100),
    provisioning_artifact_id=st.text(alphabet=ASCII_ALPHANUMERIC + '-', min_size=1, max_size=100)
)
@settings(max_examples=100)
def test_project_service_catalog_provisioning(title, project_name, product_id, provisioning_artifact_id):
    """Test Project with ServiceCatalogProvisioningDetails property."""
    project = sm.Project(title)
    project.ProjectName = project_name
    
    # Create ServiceCatalogProvisioningDetails
    provisioning = sm.ServiceCatalogProvisioningDetails()
    provisioning.ProductId = product_id
    provisioning.ProvisioningArtifactId = provisioning_artifact_id
    
    project.ServiceCatalogProvisioningDetails = provisioning
    
    # Serialize
    dict_repr = project.to_dict()
    
    # Verify nested object is serialized
    assert 'ServiceCatalogProvisioningDetails' in dict_repr['Properties']
    scp = dict_repr['Properties']['ServiceCatalogProvisioningDetails']
    assert scp['ProductId'] == product_id
    assert scp['ProvisioningArtifactId'] == provisioning_artifact_id