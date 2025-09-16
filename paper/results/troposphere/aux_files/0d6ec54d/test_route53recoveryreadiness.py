"""Property-based tests for troposphere.route53recoveryreadiness module."""

import pytest
from hypothesis import assume, given, strategies as st, settings
from troposphere import Tags
from troposphere.route53recoveryreadiness import (
    Cell,
    DNSTargetResource,
    NLBResource,
    R53ResourceRecord,
    ReadinessCheck,
    RecoveryGroup,
    Resource,
    ResourceSet,
    TargetResource,
)


# Strategies for generating valid property values
name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=48),
    min_size=1,
    max_size=100,
)
arn_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc"), min_codepoint=48),
    min_size=1,
    max_size=200,
).map(lambda s: f"arn:aws:service:region:account:{s}")


# Test 1: Round-trip serialization for Cell
@given(
    cell_name=name_strategy,
    cells=st.lists(name_strategy, max_size=5),
)
def test_cell_round_trip_serialization(cell_name, cells):
    """Test that Cell objects can be serialized and deserialized correctly."""
    # Create a Cell object
    original = Cell(
        title="TestCell",
        CellName=cell_name,
        Cells=cells,
    )
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    reconstructed = Cell.from_dict("TestCell", dict_repr)
    
    # Check that the reconstructed object matches
    assert reconstructed.to_dict() == dict_repr
    assert reconstructed.properties.get("CellName") == cell_name
    assert reconstructed.properties.get("Cells") == cells


# Test 2: Round-trip serialization for ResourceSet (has required properties)
@given(
    resource_set_name=name_strategy,
    resource_set_type=st.sampled_from(["AWS::ApiGateway::Stage", "AWS::DynamoDB::Table"]),
)
def test_resourceset_round_trip_with_required_props(resource_set_name, resource_set_type):
    """Test ResourceSet serialization with required properties."""
    # Create a minimal ResourceSet with required properties
    original = ResourceSet(
        title="TestResourceSet",
        ResourceSetName=resource_set_name,
        ResourceSetType=resource_set_type,
        Resources=[],  # Required but can be empty
    )
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    reconstructed = ResourceSet.from_dict("TestResourceSet", dict_repr)
    
    # Verify round-trip
    assert reconstructed.to_dict() == dict_repr
    assert reconstructed.properties.get("ResourceSetType") == resource_set_type


# Test 3: Validation of required properties
@given(resource_set_name=name_strategy)
def test_resourceset_missing_required_property_validation(resource_set_name):
    """Test that ResourceSet validation fails when required properties are missing."""
    # Create ResourceSet without required ResourceSetType
    resource_set = ResourceSet(
        title="TestResourceSet",
        ResourceSetName=resource_set_name,
        # Missing required: ResourceSetType and Resources
    )
    
    # Validation should raise an error for missing required properties
    with pytest.raises(ValueError):
        resource_set.validate()


# Test 4: Tags concatenation property
@given(
    tags1=st.dictionaries(name_strategy, name_strategy, max_size=5),
    tags2=st.dictionaries(name_strategy, name_strategy, max_size=5),
)
def test_tags_concatenation(tags1, tags2):
    """Test that Tags objects can be concatenated with + operator."""
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    
    # Concatenate tags
    combined = t1 + t2
    
    # Verify all tags are present in combined
    combined_dict = combined.to_dict()
    
    # Check that all tags from both objects are in the result
    t1_dict = t1.to_dict()
    t2_dict = t2.to_dict()
    
    assert len(combined_dict) == len(t1_dict) + len(t2_dict)
    
    # All tags from t1 should be in combined (in order)
    for i, tag in enumerate(t1_dict):
        assert combined_dict[i] == tag
    
    # All tags from t2 should follow
    for i, tag in enumerate(t2_dict):
        assert combined_dict[len(t1_dict) + i] == tag


# Test 5: Complex nested property serialization
@given(
    domain_name=st.text(min_size=1, max_size=100).filter(lambda x: "." in x),
    record_set_id=name_strategy,
    nlb_arn=arn_strategy,
)
def test_nested_property_serialization(domain_name, record_set_id, nlb_arn):
    """Test serialization of nested AWS properties."""
    # Create nested structure
    nlb_resource = NLBResource(Arn=nlb_arn)
    r53_record = R53ResourceRecord(
        DomainName=domain_name,
        RecordSetId=record_set_id,
    )
    target_resource = TargetResource(
        NLBResource=nlb_resource,
        R53Resource=r53_record,
    )
    dns_target = DNSTargetResource(
        DomainName=domain_name,
        RecordSetId=record_set_id,
        RecordType="A",
        TargetResource=target_resource,
    )
    
    # Convert to dict
    dict_repr = dns_target.to_dict()
    
    # Verify structure is preserved
    assert dict_repr["DomainName"] == domain_name
    assert dict_repr["RecordSetId"] == record_set_id
    assert dict_repr["RecordType"] == "A"
    assert "TargetResource" in dict_repr
    assert dict_repr["TargetResource"]["NLBResource"]["Arn"] == nlb_arn
    assert dict_repr["TargetResource"]["R53Resource"]["DomainName"] == domain_name


# Test 6: RecoveryGroup with list properties
@given(
    cells=st.lists(name_strategy, min_size=1, max_size=10),
    recovery_group_name=name_strategy,
)
def test_recovery_group_list_properties(cells, recovery_group_name):
    """Test RecoveryGroup with list properties."""
    rg = RecoveryGroup(
        title="TestRecoveryGroup",
        Cells=cells,
        RecoveryGroupName=recovery_group_name,
    )
    
    # Convert to dict and verify
    dict_repr = rg.to_dict()
    assert dict_repr["Properties"]["Cells"] == cells
    assert dict_repr["Properties"]["RecoveryGroupName"] == recovery_group_name
    
    # Round-trip test
    reconstructed = RecoveryGroup.from_dict("TestRecoveryGroup", dict_repr)
    assert reconstructed.to_dict() == dict_repr


# Test 7: ReadinessCheck property handling
@given(
    check_name=name_strategy,
    resource_set_name=name_strategy,
)
def test_readiness_check_properties(check_name, resource_set_name):
    """Test ReadinessCheck object creation and serialization."""
    rc = ReadinessCheck(
        title="TestCheck",
        ReadinessCheckName=check_name,
        ResourceSetName=resource_set_name,
    )
    
    dict_repr = rc.to_dict()
    assert dict_repr["Properties"]["ReadinessCheckName"] == check_name
    assert dict_repr["Properties"]["ResourceSetName"] == resource_set_name
    
    # Verify type is set correctly
    assert dict_repr["Type"] == "AWS::Route53RecoveryReadiness::ReadinessCheck"


# Test 8: Resource with optional properties
@given(
    component_id=name_strategy,
    resource_arn=arn_strategy,
    readiness_scopes=st.lists(name_strategy, max_size=5),
)
def test_resource_optional_properties(component_id, resource_arn, readiness_scopes):
    """Test Resource with various optional properties."""
    resource = Resource(
        ComponentId=component_id,
        ResourceArn=resource_arn,
        ReadinessScopes=readiness_scopes,
    )
    
    dict_repr = resource.to_dict()
    assert dict_repr["ComponentId"] == component_id
    assert dict_repr["ResourceArn"] == resource_arn
    assert dict_repr["ReadinessScopes"] == readiness_scopes


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--tb=short"])