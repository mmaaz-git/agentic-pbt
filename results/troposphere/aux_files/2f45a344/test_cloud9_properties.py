import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.cloud9 as cloud9
from troposphere import Tags

# Strategy for valid strings (URLs and paths)
text_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
url_strategy = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1, max_size=200)

# Strategy for valid AutomaticStopTimeMinutes (positive integers)
stop_time_strategy = st.integers(min_value=0, max_value=20160)  # AWS limit is 20160 minutes (14 days)

# Strategy for connection types 
connection_type_strategy = st.sampled_from(["CONNECT_SSH", "CONNECT_SSM"])

# Strategy for instance types (common EC2 instance types)
instance_type_strategy = st.sampled_from([
    "t2.micro", "t2.small", "t2.medium", "t3.micro", "t3.small", "m5.large"
])

# Strategy for image IDs (AWS AMI format)
image_id_strategy = st.from_regex(r"ami-[a-f0-9]{8,17}", fullmatch=True)

# Strategy for AWS ARNs
arn_strategy = st.from_regex(r"arn:aws:[a-z0-9\-]+:[a-z0-9\-]*:[0-9]{12}:[a-zA-Z0-9\-_/]+", fullmatch=True)

# Strategy for subnet IDs
subnet_id_strategy = st.from_regex(r"subnet-[a-f0-9]{8,17}", fullmatch=True)


@given(
    path_component=text_strategy,
    repository_url=url_strategy
)
def test_repository_round_trip(path_component, repository_url):
    """Test that Repository objects survive to_dict/from_dict round-trip"""
    original = cloud9.Repository(
        PathComponent=path_component,
        RepositoryUrl=repository_url
    )
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    reconstructed = cloud9.Repository._from_dict(**dict_repr)
    
    # They should be equal
    assert original == reconstructed
    assert original.to_dict() == reconstructed.to_dict()


@given(
    automatic_stop=st.one_of(st.none(), stop_time_strategy),
    connection_type=st.one_of(st.none(), connection_type_strategy),
    description=st.one_of(st.none(), text_strategy),
    image_id=image_id_strategy,
    instance_type=instance_type_strategy,
    name=st.one_of(st.none(), st.from_regex(r"[a-zA-Z0-9][a-zA-Z0-9\-]{0,59}", fullmatch=True)),
    owner_arn=st.one_of(st.none(), arn_strategy),
    subnet_id=st.one_of(st.none(), subnet_id_strategy)
)
@settings(max_examples=100)
def test_environment_ec2_round_trip(
    automatic_stop, connection_type, description, 
    image_id, instance_type, name, owner_arn, subnet_id
):
    """Test that EnvironmentEC2 objects survive to_dict/from_dict round-trip"""
    kwargs = {
        "ImageId": image_id,
        "InstanceType": instance_type
    }
    
    # Add optional fields if provided
    if automatic_stop is not None:
        kwargs["AutomaticStopTimeMinutes"] = automatic_stop
    if connection_type is not None:
        kwargs["ConnectionType"] = connection_type
    if description is not None:
        kwargs["Description"] = description
    if name is not None:
        kwargs["Name"] = name
    if owner_arn is not None:
        kwargs["OwnerArn"] = owner_arn
    if subnet_id is not None:
        kwargs["SubnetId"] = subnet_id
    
    original = cloud9.EnvironmentEC2("TestEnv", **kwargs)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    
    # Extract Properties for reconstruction
    if "Properties" in dict_repr:
        props = dict_repr["Properties"]
        reconstructed = cloud9.EnvironmentEC2.from_dict("TestEnv", props)
        
        # They should be equal
        assert original == reconstructed
        assert original.to_dict() == reconstructed.to_dict()


@given(
    path_component=text_strategy,
    repository_url=url_strategy
)
def test_repository_equality(path_component, repository_url):
    """Test that Repository objects with same data are equal"""
    repo1 = cloud9.Repository(
        PathComponent=path_component,
        RepositoryUrl=repository_url
    )
    repo2 = cloud9.Repository(
        PathComponent=path_component,
        RepositoryUrl=repository_url
    )
    
    assert repo1 == repo2
    assert hash(json.dumps(repo1.to_dict(), sort_keys=True)) == hash(json.dumps(repo2.to_dict(), sort_keys=True))


@given(
    automatic_stop=st.integers(min_value=-1000000, max_value=1000000)
)
def test_automatic_stop_time_validation(automatic_stop):
    """Test that AutomaticStopTimeMinutes accepts any integer value"""
    # The integer validator should accept any integer
    env = cloud9.EnvironmentEC2(
        "TestEnv",
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        AutomaticStopTimeMinutes=automatic_stop
    )
    
    # Should be able to convert to dict without error
    dict_repr = env.to_dict()
    assert "Properties" in dict_repr
    assert dict_repr["Properties"]["AutomaticStopTimeMinutes"] == automatic_stop


@given(
    repos=st.lists(
        st.builds(
            cloud9.Repository,
            PathComponent=text_strategy,
            RepositoryUrl=url_strategy
        ),
        min_size=0,
        max_size=5
    )
)
def test_repositories_list_property(repos):
    """Test that EnvironmentEC2 can accept a list of Repository objects"""
    env = cloud9.EnvironmentEC2(
        "TestEnv",
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        Repositories=repos
    )
    
    dict_repr = env.to_dict()
    assert "Properties" in dict_repr
    
    # Repositories should be serialized as a list of dicts
    if repos:
        assert "Repositories" in dict_repr["Properties"]
        assert len(dict_repr["Properties"]["Repositories"]) == len(repos)
        
        # Each repository should be properly serialized
        for i, repo in enumerate(repos):
            assert dict_repr["Properties"]["Repositories"][i] == repo.to_dict()


@given(st.data())
def test_required_fields_validation(data):
    """Test that missing required fields raise appropriate errors"""
    # Test Repository missing required fields
    try:
        repo = cloud9.Repository()
        repo.to_dict()  # This should trigger validation
        assert False, "Should have raised ValueError for missing required fields"
    except ValueError as e:
        assert "required" in str(e).lower()
    
    # Test with only one required field
    try:
        repo = cloud9.Repository(PathComponent="test")
        repo.to_dict()
        assert False, "Should have raised ValueError for missing RepositoryUrl"
    except ValueError as e:
        assert "required" in str(e).lower()
    
    # Test EnvironmentEC2 missing required fields
    try:
        env = cloud9.EnvironmentEC2("TestEnv")
        env.to_dict()
        assert False, "Should have raised ValueError for missing required fields"
    except ValueError as e:
        assert "required" in str(e).lower()