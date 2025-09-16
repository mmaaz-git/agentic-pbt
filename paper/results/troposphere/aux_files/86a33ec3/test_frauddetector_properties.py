"""Property-based tests for troposphere.frauddetector module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.frauddetector as fd
from troposphere import Tags
import pytest


# Strategy for generating valid names (alphanumeric strings)
valid_name_strategy = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=255)
valid_description_strategy = st.text(min_size=0, max_size=1000)


# Property 1: Resource types should match class attribute
@given(
    name=valid_name_strategy,
    description=valid_description_strategy
)
def test_resource_type_invariant(name, description):
    """Test that resource_type in class matches Type in to_dict output."""
    # Test with EntityType
    entity = fd.EntityType("TestEntity", Name=name, Description=description)
    result = entity.to_dict()
    assert result["Type"] == entity.resource_type
    assert entity.resource_type == "AWS::FraudDetector::EntityType"
    
    # Test with Label
    label = fd.Label("TestLabel", Name=name, Description=description)
    result = label.to_dict()
    assert result["Type"] == label.resource_type
    assert label.resource_type == "AWS::FraudDetector::Label"
    
    # Test with Outcome
    outcome = fd.Outcome("TestOutcome", Name=name, Description=description)
    result = outcome.to_dict()
    assert result["Type"] == outcome.resource_type
    assert outcome.resource_type == "AWS::FraudDetector::Outcome"


# Property 2: to_dict should always have Type and Properties keys for AWSObject subclasses
@given(
    name=valid_name_strategy,
    description=st.one_of(st.none(), valid_description_strategy)
)
def test_to_dict_structure(name, description):
    """Test that to_dict always returns proper structure."""
    # Test various AWSObject subclasses
    entity = fd.EntityType("TestEntity", Name=name)
    if description is not None:
        entity.Description = description
    
    result = entity.to_dict()
    assert isinstance(result, dict)
    assert "Type" in result
    assert "Properties" in result
    assert isinstance(result["Properties"], dict)
    assert result["Properties"]["Name"] == name
    if description is not None:
        assert result["Properties"]["Description"] == description


# Property 3: Properties set in constructor should appear in to_dict output
@given(
    name=valid_name_strategy,
    data_source=st.sampled_from(["EVENT", "EXTERNAL_MODEL_SCORE", "MODEL_SCORE"]),
    data_type=st.sampled_from(["STRING", "INTEGER", "FLOAT", "BOOLEAN"]),
    default_value=valid_name_strategy,
    description=st.one_of(st.none(), valid_description_strategy)
)
def test_variable_properties_roundtrip(name, data_source, data_type, default_value, description):
    """Test that Variable properties set in constructor appear in to_dict."""
    kwargs = {
        "Name": name,
        "DataSource": data_source, 
        "DataType": data_type,
        "DefaultValue": default_value
    }
    if description is not None:
        kwargs["Description"] = description
    
    var = fd.Variable("TestVar", **kwargs)
    result = var.to_dict()
    
    assert result["Type"] == "AWS::FraudDetector::Variable"
    props = result["Properties"]
    assert props["Name"] == name
    assert props["DataSource"] == data_source
    assert props["DataType"] == data_type
    assert props["DefaultValue"] == default_value
    if description is not None:
        assert props["Description"] == description


# Property 4: List class should not conflict with built-in list
@given(
    name=valid_name_strategy,
    elements=st.lists(valid_name_strategy, min_size=0, max_size=10)
)
def test_list_class_no_conflict(name, elements):
    """Test that fd.List doesn't interfere with built-in list."""
    # Create a fd.List object
    fraud_list = fd.List("TestList", Name=name)
    if elements:
        fraud_list.Elements = elements
    
    # Verify it's the right type
    assert isinstance(fraud_list, fd.List)
    assert not isinstance(fraud_list, list)
    
    # Verify built-in list still works
    python_list = list(range(5))
    assert isinstance(python_list, list)
    assert not isinstance(python_list, fd.List)
    
    # Verify to_dict works
    result = fraud_list.to_dict()
    assert result["Type"] == "AWS::FraudDetector::List"
    assert result["Properties"]["Name"] == name
    if elements:
        assert result["Properties"]["Elements"] == elements


# Property 5: Required properties must be provided
def test_required_properties_enforcement():
    """Test that missing required properties raise errors."""
    # EntityType requires Name
    with pytest.raises(ValueError) as exc_info:
        entity = fd.EntityType("TestEntity")
        entity.to_dict()
    assert "Resource TestEntity required in type AWS::FraudDetector::EntityType" in str(exc_info.value)
    
    # Variable requires multiple fields
    with pytest.raises(ValueError) as exc_info:
        var = fd.Variable("TestVar", Name="test")  # Missing DataSource, DataType, DefaultValue
        var.to_dict()
    assert "Resource TestVar required in type AWS::FraudDetector::Variable" in str(exc_info.value)


# Property 6: Optional properties are truly optional
@given(name=valid_name_strategy)
def test_optional_properties(name):
    """Test that objects can be created with only required properties."""
    # EntityType with only required Name property
    entity = fd.EntityType("TestEntity", Name=name)
    result = entity.to_dict()
    assert result["Properties"]["Name"] == name
    assert "Description" not in result["Properties"]  # Optional property not included
    
    # Label with only required Name property  
    label = fd.Label("TestLabel", Name=name)
    result = label.to_dict()
    assert result["Properties"]["Name"] == name
    assert "Description" not in result["Properties"]


# Property 7: Complex nested structures (Detector with Rules and Outcomes)
@given(
    detector_id=valid_name_strategy,
    rule_id=valid_name_strategy,
    rule_expression=st.text(min_size=1, max_size=100),
    outcome_name=valid_name_strategy
)
def test_nested_structures(detector_id, rule_id, rule_expression, outcome_name):
    """Test that complex nested structures work correctly."""
    # Create nested components
    outcome = fd.OutcomeProperty(Name=outcome_name)
    rule = fd.Rule(
        RuleId=rule_id,
        Expression=rule_expression,
        Language="DETECTORPL",
        Outcomes=[outcome]
    )
    event_type = fd.EventTypeProperty(
        Name="test_event",
        EntityTypes=[],
        EventVariables=[]
    )
    
    # Create Detector with nested structures
    detector = fd.Detector(
        "TestDetector",
        DetectorId=detector_id,
        EventType=event_type,
        Rules=[rule]
    )
    
    result = detector.to_dict()
    assert result["Type"] == "AWS::FraudDetector::Detector"
    props = result["Properties"]
    assert props["DetectorId"] == detector_id
    assert len(props["Rules"]) == 1
    assert props["Rules"][0]["RuleId"] == rule_id
    assert props["Rules"][0]["Expression"] == rule_expression
    assert props["Rules"][0]["Outcomes"][0]["Name"] == outcome_name


# Property 8: Title validation  
@given(
    title=st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=1)
)
def test_title_validation(title):
    """Test that title validation works correctly."""
    # Titles must match the regex ^[a-zA-Z0-9]+$
    valid_title_chars = all(c.isalnum() for c in title)
    
    if valid_title_chars and title:
        # Should succeed
        entity = fd.EntityType(title, Name="test")
        assert entity.title == title
    else:
        # Should fail validation
        with pytest.raises(ValueError) as exc_info:
            entity = fd.EntityType(title, Name="test")
        assert "alphanumeric" in str(exc_info.value).lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])