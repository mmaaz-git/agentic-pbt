"""Property-based tests for troposphere.sagemaker module."""

import json
from hypothesis import assume, given, strategies as st, settings
import troposphere.sagemaker as sm
import troposphere
import inspect


# Strategy for generating valid AWS resource names
resource_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-"),
    min_size=1,
    max_size=63
).filter(lambda x: x[0].isalpha() and not x.endswith('-'))

# Strategy for ARNs
arn_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters=":/-_"),
    min_size=20,
    max_size=200
).map(lambda x: f"arn:aws:iam::123456789012:role/{x}")

# Strategy for VPC IDs
vpc_id_strategy = st.text(min_size=4, max_size=20).map(lambda x: f"vpc-{x}")

# Strategy for subnet IDs
subnet_id_strategy = st.text(min_size=4, max_size=20).map(lambda x: f"subnet-{x}")


@given(
    title=resource_name_strategy,
    domain_name=resource_name_strategy,
    vpc_id=vpc_id_strategy,
    subnet_ids=st.lists(subnet_id_strategy, min_size=1, max_size=5),
    auth_mode=st.sampled_from(['IAM', 'SSO'])
)
@settings(max_examples=100)
def test_domain_round_trip_property(title, domain_name, vpc_id, subnet_ids, auth_mode):
    """Test that Domain objects can round-trip through dict serialization."""
    # Create domain
    domain = sm.Domain(title)
    domain.DomainName = domain_name
    domain.VpcId = vpc_id
    domain.SubnetIds = subnet_ids
    domain.AuthMode = auth_mode
    domain.DefaultUserSettings = sm.UserSettings()
    
    # Serialize to dict
    dict_repr = domain.to_dict()
    
    # Deserialize - using Properties only since that's what from_dict expects
    properties = dict_repr.get('Properties', {})
    new_domain = sm.Domain.from_dict(title + '2', properties)
    new_dict = new_domain.to_dict()
    
    # Check that Properties are preserved
    assert dict_repr.get('Properties') == new_dict.get('Properties')
    

@given(
    title=resource_name_strategy,
    space_name=resource_name_strategy,
    domain_id=st.text(min_size=1, max_size=50)
)
@settings(max_examples=100)
def test_space_round_trip_property(title, space_name, domain_id):
    """Test that Space objects can round-trip through dict serialization."""
    space = sm.Space(title)
    space.SpaceName = space_name
    space.DomainId = domain_id
    
    dict_repr = space.to_dict()
    properties = dict_repr.get('Properties', {})
    new_space = sm.Space.from_dict(title + '2', properties)
    new_dict = new_space.to_dict()
    
    assert dict_repr.get('Properties') == new_dict.get('Properties')


@given(
    title=resource_name_strategy,
    model_name=resource_name_strategy,
    execution_role_arn=arn_strategy,
    enable_network_isolation=st.booleans()
)
@settings(max_examples=100)
def test_model_json_serialization(title, model_name, execution_role_arn, enable_network_isolation):
    """Test that Model objects can be serialized to/from JSON."""
    model = sm.Model(title)
    model.ModelName = model_name
    model.ExecutionRoleArn = execution_role_arn
    model.EnableNetworkIsolation = enable_network_isolation
    
    # Serialize to JSON
    json_str = model.to_json()
    
    # Should be valid JSON
    json_dict = json.loads(json_str)
    
    # Should have expected structure
    assert 'Type' in json_dict
    assert 'Properties' in json_dict
    assert json_dict['Type'] == 'AWS::SageMaker::Model'
    assert json_dict['Properties']['ModelName'] == model_name
    assert json_dict['Properties']['ExecutionRoleArn'] == execution_role_arn
    

@given(
    title=resource_name_strategy,
    notebook_name=resource_name_strategy,
    role_arn=arn_strategy,
    instance_type=st.sampled_from(['ml.t2.medium', 'ml.t3.medium', 'ml.m5.xlarge'])
)
@settings(max_examples=100)
def test_notebook_instance_validation(title, notebook_name, role_arn, instance_type):
    """Test NotebookInstance validation and serialization."""
    notebook = sm.NotebookInstance(title)
    notebook.NotebookInstanceName = notebook_name
    notebook.RoleArn = role_arn
    notebook.InstanceType = instance_type
    
    # Should validate without errors
    errors = notebook.validate()
    assert errors == []
    
    # Should serialize successfully
    dict_repr = notebook.to_dict()
    assert dict_repr['Properties']['NotebookInstanceName'] == notebook_name
    

@given(
    title=resource_name_strategy,
    endpoint_name=resource_name_strategy,
    endpoint_config_name=resource_name_strategy
)
@settings(max_examples=100)
def test_endpoint_properties(title, endpoint_name, endpoint_config_name):
    """Test Endpoint class properties and methods."""
    endpoint = sm.Endpoint(title)
    endpoint.EndpointName = endpoint_name
    endpoint.EndpointConfigName = endpoint_config_name
    
    # Test to_dict
    dict_repr = endpoint.to_dict()
    assert dict_repr['Type'] == 'AWS::SageMaker::Endpoint'
    assert dict_repr['Properties']['EndpointName'] == endpoint_name
    
    # Test from_dict round-trip
    properties = dict_repr['Properties']
    new_endpoint = sm.Endpoint.from_dict(title + '2', properties)
    
    # Properties should be preserved
    assert new_endpoint.EndpointName == endpoint_name
    assert new_endpoint.EndpointConfigName == endpoint_config_name
    

# Test for finding classes with incorrect round-trip behavior
def test_all_classes_round_trip_format():
    """Test that all AWS resource classes have consistent to_dict/from_dict format."""
    classes = [(name, obj) for name, obj in inspect.getmembers(sm) 
               if inspect.isclass(obj) and hasattr(obj, 'props') and hasattr(obj, 'resource_type')]
    
    inconsistent_classes = []
    
    for name, cls in classes:
        try:
            # Create minimal instance
            instance = cls(f'Test{name}')
            
            # Get to_dict output
            dict_repr = instance.to_dict()
            
            # Try to use from_dict with full dict (should fail)
            try:
                cls.from_dict(f'Test{name}2', dict_repr)
                # If this succeeds, format is consistent
            except (AttributeError, KeyError) as e:
                if 'does not have a Properties property' in str(e):
                    # This is the inconsistency we're looking for
                    inconsistent_classes.append(name)
                    
        except Exception:
            # Skip classes that require mandatory properties
            pass
    
    # This test demonstrates the API inconsistency
    assert len(inconsistent_classes) > 0, "Expected to find classes with to_dict/from_dict inconsistency"
    

@given(
    title=resource_name_strategy,
    image_uri=st.text(min_size=1, max_size=255),
    model_data_url=st.text(min_size=1, max_size=255).map(lambda x: f"s3://bucket/{x}")
)
@settings(max_examples=100)
def test_container_definition_properties(title, image_uri, model_data_url):
    """Test ContainerDefinition as an AWSProperty."""
    container = sm.ContainerDefinition()
    container.Image = image_uri
    container.ModelDataUrl = model_data_url
    
    # Should be able to convert to dict
    dict_repr = container.to_dict()
    assert dict_repr['Image'] == image_uri
    assert dict_repr['ModelDataUrl'] == model_data_url
    

@given(
    title=resource_name_strategy,
    project_name=resource_name_strategy,
    service_catalog_provisioning=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=5
    )
)
@settings(max_examples=100)
def test_project_with_service_catalog(title, project_name, service_catalog_provisioning):
    """Test Project with ServiceCatalogProvisioningDetails."""
    project = sm.Project(title)
    project.ProjectName = project_name
    
    # Create ServiceCatalogProvisioningDetails
    provisioning = sm.ServiceCatalogProvisioningDetails()
    provisioning.ProductId = 'prod-123'
    provisioning.ProvisioningArtifactId = 'pa-123'
    
    project.ServiceCatalogProvisioningDetails = provisioning
    
    # Should serialize correctly
    dict_repr = project.to_dict()
    assert 'ServiceCatalogProvisioningDetails' in dict_repr['Properties']
    assert dict_repr['Properties']['ServiceCatalogProvisioningDetails']['ProductId'] == 'prod-123'
    

@given(
    title=resource_name_strategy,
    tags=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50),
            st.text(min_size=0, max_size=100)
        ),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100)
def test_tags_handling(title, tags):
    """Test that Tags are handled correctly."""
    model = sm.Model(title)
    model.ExecutionRoleArn = 'arn:aws:iam::123456789012:role/TestRole'
    
    # Create Tags object
    tags_obj = troposphere.Tags()
    for key, value in tags:
        tags_obj.add(key, value)
    
    model.Tags = tags_obj
    
    # Should serialize correctly
    dict_repr = model.to_dict()
    
    # Tags should be in Properties
    if tags:
        assert 'Tags' in dict_repr['Properties']
        assert len(dict_repr['Properties']['Tags']) == len(tags)