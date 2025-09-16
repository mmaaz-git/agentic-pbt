"""Property-based tests for troposphere.neptunegraph module"""

import sys
import json
from hypothesis import given, strategies as st, assume, settings, example
import pytest

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators
from troposphere.neptunegraph import Graph, PrivateGraphEndpoint, VectorSearchConfiguration
from troposphere import AWSHelperFn, Ref


# Test 1: Boolean validator consistency
@given(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False", "1", "0"]))
def test_boolean_validator_consistency(value):
    """Test that boolean validator handles documented values correctly"""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    
    # Check mapping consistency
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


# Test 2: Boolean validator invalid values
@given(st.one_of(
    st.text().filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_values(value):
    """Test that boolean validator raises ValueError for invalid inputs"""
    with pytest.raises(ValueError):
        validators.boolean(value)


# Test 3: Integer validator round-trip property
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.lstrip('-').isdigit()),  # String representations of integers
))
def test_integer_validator_round_trip(value):
    """Test that integer validator preserves integer values"""
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        # Skip values that can't be converted to int
        assume(False)
    
    result = validators.integer(value)
    # The validator returns the original value if it's valid
    assert int(result) == int_value


# Test 4: Integer validator invalid values  
@given(st.one_of(
    st.text().filter(lambda x: not x.lstrip('-').isdigit() and x != ''),
    st.floats(allow_nan=True, allow_infinity=True).filter(lambda x: not x.is_integer()),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator_invalid_values(value):
    """Test that integer validator raises ValueError for non-integer inputs"""
    # Skip empty strings as they might be considered valid in some contexts
    if value == '':
        assume(False)
    
    with pytest.raises(ValueError):
        validators.integer(value)


# Test 5: Title validation for alphanumeric constraint
@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
def test_title_validation(title):
    """Test that Graph title validation works correctly"""
    graph = Graph.no_validation(Graph(title=None, ProvisionedMemory=1024))
    
    # Override the title after creation to test validation
    graph.title = title
    
    try:
        graph.validate_title()
        # If validation passes, title should be alphanumeric
        assert title and all(c.isalnum() for c in title)
    except ValueError:
        # If validation fails, title should be non-alphanumeric or empty
        assert not title or not all(c.isalnum() for c in title)


# Test 6: Graph class required property validation
@given(
    graph_name=st.one_of(st.none(), st.text()),
    deletion_protection=st.one_of(st.none(), st.booleans()),
    public_connectivity=st.one_of(st.none(), st.booleans()),
    replica_count=st.one_of(st.none(), st.integers(min_value=0, max_value=10)),
)
def test_graph_required_property_validation(graph_name, deletion_protection, 
                                           public_connectivity, replica_count):
    """Test that Graph validates required ProvisionedMemory property"""
    kwargs = {}
    if graph_name is not None:
        kwargs['GraphName'] = graph_name
    if deletion_protection is not None:
        kwargs['DeletionProtection'] = deletion_protection
    if public_connectivity is not None:
        kwargs['PublicConnectivity'] = public_connectivity
    if replica_count is not None:
        kwargs['ReplicaCount'] = replica_count
    
    # Graph requires ProvisionedMemory - should fail without it
    with pytest.raises(ValueError, match="ProvisionedMemory"):
        graph = Graph("TestGraph", **kwargs)
        graph.to_dict()  # This triggers validation


# Test 7: Graph with valid required properties
@given(
    provisioned_memory=st.integers(min_value=1, max_value=1000000),
    graph_name=st.one_of(st.none(), st.text(min_size=1, max_size=63)),
    deletion_protection=st.one_of(st.none(), st.booleans()),
)
def test_graph_with_valid_properties(provisioned_memory, graph_name, deletion_protection):
    """Test that Graph works with valid required properties"""
    kwargs = {'ProvisionedMemory': provisioned_memory}
    if graph_name is not None:
        kwargs['GraphName'] = graph_name
    if deletion_protection is not None:
        kwargs['DeletionProtection'] = deletion_protection
    
    graph = Graph("TestGraph", **kwargs)
    result = graph.to_dict()
    
    assert result['Type'] == 'AWS::NeptuneGraph::Graph'
    assert result['Properties']['ProvisionedMemory'] == provisioned_memory


# Test 8: VectorSearchConfiguration dimension validation
@given(dimension=st.integers())
def test_vector_search_configuration_dimension(dimension):
    """Test VectorSearchConfiguration with various dimension values"""
    config = VectorSearchConfiguration(VectorSearchDimension=dimension)
    result = config.to_dict()
    assert result['VectorSearchDimension'] == dimension


# Test 9: PrivateGraphEndpoint required properties
@given(
    graph_id=st.text(min_size=1, max_size=100),
    vpc_id=st.text(min_size=1, max_size=100),
    security_groups=st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=50), max_size=5)),
    subnet_ids=st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=50), max_size=5))
)
def test_private_graph_endpoint_properties(graph_id, vpc_id, security_groups, subnet_ids):
    """Test PrivateGraphEndpoint with required and optional properties"""
    kwargs = {
        'GraphIdentifier': graph_id,
        'VpcId': vpc_id
    }
    if security_groups is not None:
        kwargs['SecurityGroupIds'] = security_groups
    if subnet_ids is not None:
        kwargs['SubnetIds'] = subnet_ids
    
    endpoint = PrivateGraphEndpoint("TestEndpoint", **kwargs)
    result = endpoint.to_dict()
    
    assert result['Type'] == 'AWS::NeptuneGraph::PrivateGraphEndpoint'
    assert result['Properties']['GraphIdentifier'] == graph_id
    assert result['Properties']['VpcId'] == vpc_id


# Test 10: to_dict/from_dict round-trip for Graph
@given(
    provisioned_memory=st.integers(min_value=1, max_value=1000000),
    graph_name=st.text(min_size=1, max_size=63),
    deletion_protection=st.booleans(),
    replica_count=st.integers(min_value=1, max_value=10)
)
def test_graph_to_dict_from_dict_round_trip(provisioned_memory, graph_name, 
                                            deletion_protection, replica_count):
    """Test that Graph objects can round-trip through to_dict/from_dict"""
    # Create original graph
    original = Graph(
        "TestGraph",
        ProvisionedMemory=provisioned_memory,
        GraphName=graph_name,
        DeletionProtection=deletion_protection,
        ReplicaCount=replica_count
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Extract properties for from_dict
    props = dict_repr.get('Properties', {})
    
    # Create new graph from dict
    restored = Graph.from_dict("TestGraph", props)
    
    # Compare the dictionaries
    assert original.to_dict() == restored.to_dict()


# Test 11: Property type validation
@given(
    invalid_memory=st.one_of(
        st.text().filter(lambda x: not x.lstrip('-').isdigit()),
        st.floats(),
        st.lists(st.integers()),
        st.none()
    )
)  
def test_graph_invalid_provisioned_memory_type(invalid_memory):
    """Test that Graph rejects invalid types for ProvisionedMemory"""
    # Skip valid string integers
    if isinstance(invalid_memory, str) and invalid_memory.lstrip('-').isdigit():
        assume(False)
    
    with pytest.raises((TypeError, ValueError)):
        graph = Graph("TestGraph", ProvisionedMemory=invalid_memory)
        graph.to_dict()  # Trigger validation


# Test 12: Test numeric string handling in validators
@given(st.text())
def test_integer_validator_string_handling(value):
    """Test how integer validator handles various string inputs"""
    try:
        result = validators.integer(value)
        # If it succeeds, we should be able to convert both to int
        assert int(result) == int(value)
    except ValueError:
        # If integer validator fails, int() should also fail
        with pytest.raises((ValueError, TypeError)):
            int(value)