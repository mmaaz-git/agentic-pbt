"""Property-based tests for troposphere.iotthingsgraph module"""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.iotthingsgraph import DefinitionDocument, FlowTemplate
from troposphere.validators import double


# Test 1: Double validator properties
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_validator_accepts_valid_floats(x):
    """The double validator should accept valid float values and preserve them."""
    result = double(x)
    assert result == x
    

@given(st.integers())
def test_double_validator_accepts_integers(x):
    """The double validator should accept integer values."""
    result = double(x)
    assert result == x


@given(st.text(min_size=1).filter(lambda x: not x.strip().replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit()))
def test_double_validator_rejects_non_numeric_strings(x):
    """The double validator should reject non-numeric string values."""
    # Filter out strings that could be parsed as numbers
    try:
        float(x)
        assume(False)  # Skip if it's actually parseable as float
    except (ValueError, TypeError):
        pass
    
    with pytest.raises(ValueError, match="is not a valid double"):
        double(x)


@given(st.one_of(st.none(), st.lists(st.integers()), st.dictionaries(st.text(), st.text())))
def test_double_validator_rejects_non_numeric_types(x):
    """The double validator should reject non-numeric types."""
    with pytest.raises(ValueError, match="is not a valid double"):
        double(x)


# Test 2: Title validation for AWSObject
@given(st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122).filter(str.isalnum), min_size=1))
def test_valid_alphanumeric_titles_accepted(title):
    """AWSObject titles containing only alphanumeric characters should be accepted."""
    definition = DefinitionDocument(Language="GRAPHQL", Text="{}")
    obj = FlowTemplate(title, Definition=definition)
    assert obj.title == title


@given(st.text(min_size=1).filter(lambda x: not x.replace('_', '').replace('-', '').replace(' ', '').replace('.', '').isalnum()))
def test_invalid_titles_rejected(title):
    """AWSObject titles with non-alphanumeric characters should be rejected."""
    # Ensure we have at least one non-alphanumeric character
    if title.isalnum():
        assume(False)
    
    definition = DefinitionDocument(Language="GRAPHQL", Text="{}")
    with pytest.raises(ValueError, match='Name ".*" not alphanumeric'):
        FlowTemplate(title, Definition=definition)


# Test 3: Required field validation
def test_definition_document_requires_language_and_text():
    """DefinitionDocument should require both Language and Text properties."""
    # Missing Language
    doc = DefinitionDocument(Text="{}")
    with pytest.raises(ValueError, match="Resource Language required"):
        doc.to_dict()
    
    # Missing Text
    doc = DefinitionDocument(Language="GRAPHQL")
    with pytest.raises(ValueError, match="Resource Text required"):
        doc.to_dict()
    
    # Both present should work
    doc = DefinitionDocument(Language="GRAPHQL", Text="{}")
    result = doc.to_dict()
    assert "Language" in result
    assert "Text" in result


def test_flow_template_requires_definition():
    """FlowTemplate should require Definition property."""
    # Missing Definition
    obj = FlowTemplate("TestTemplate")
    with pytest.raises(ValueError, match="Resource Definition required"):
        obj.to_dict()
    
    # With Definition should work
    definition = DefinitionDocument(Language="GRAPHQL", Text="{}")
    obj = FlowTemplate("TestTemplate", Definition=definition)
    result = obj.to_dict()
    assert "Properties" in result
    assert "Definition" in result["Properties"]


# Test 4: Type enforcement
@given(st.one_of(st.integers(), st.floats(), st.lists(st.text()), st.dictionaries(st.text(), st.text())))
def test_definition_property_type_enforcement(invalid_value):
    """FlowTemplate.Definition should only accept DefinitionDocument instances."""
    with pytest.raises(TypeError):
        FlowTemplate("Test", Definition=invalid_value)


@given(st.one_of(st.integers(), st.floats(), st.lists(st.text()), st.dictionaries(st.text(), st.text())))
def test_string_property_type_enforcement(invalid_value):
    """DefinitionDocument string properties should only accept strings."""
    # Test Language property
    with pytest.raises(TypeError):
        DefinitionDocument(Language=invalid_value, Text="{}")
    
    # Test Text property
    with pytest.raises(TypeError):
        DefinitionDocument(Language="GRAPHQL", Text=invalid_value)


# Test 5: to_dict/from_dict round-trip
@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122).filter(str.isalnum), min_size=1),
    st.text(min_size=1),
    st.text(min_size=1),
    st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=1000))
)
def test_flow_template_dict_round_trip(title, language, text, version):
    """FlowTemplate should preserve data through to_dict/from_dict conversion."""
    # Create original object
    definition = DefinitionDocument(Language=language, Text=text)
    kwargs = {"Definition": definition}
    if version is not None:
        kwargs["CompatibleNamespaceVersion"] = version
    
    original = FlowTemplate(title, **kwargs)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Create new object from dict (stripping the Type field)
    props = dict_repr.get("Properties", {})
    new_obj = FlowTemplate.from_dict(title, props)
    
    # Compare
    assert new_obj.title == original.title
    assert new_obj.to_dict() == original.to_dict()


@given(st.text(min_size=1), st.text(min_size=1))
def test_definition_document_dict_round_trip(language, text):
    """DefinitionDocument should preserve data through to_dict/from_dict conversion."""
    # Create original
    original = DefinitionDocument(Language=language, Text=text)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Create new from dict
    new_obj = DefinitionDocument._from_dict(**dict_repr)
    
    # Compare
    assert new_obj.to_dict() == original.to_dict()


# Test 6: Property access patterns
@given(st.text(min_size=1), st.text(min_size=1))
def test_definition_document_property_access(language, text):
    """Properties should be accessible via attribute access."""
    doc = DefinitionDocument(Language=language, Text=text)
    assert doc.Language == language
    assert doc.Text == text


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=1000))
def test_flow_template_optional_property(version):
    """Optional properties should be settable and retrievable."""
    definition = DefinitionDocument(Language="GRAPHQL", Text="{}")
    template = FlowTemplate("Test", Definition=definition, CompatibleNamespaceVersion=version)
    assert template.CompatibleNamespaceVersion == version
    
    # Should appear in dict
    result = template.to_dict()
    assert result["Properties"]["CompatibleNamespaceVersion"] == version


# Test 7: JSON serialization
@given(st.text(min_size=1), st.text(min_size=1))
def test_definition_document_json_serialization(language, text):
    """DefinitionDocument should be JSON serializable."""
    doc = DefinitionDocument(Language=language, Text=text)
    json_str = doc.to_json(validation=False)
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed["Language"] == language
    assert parsed["Text"] == text
    
    # Round-trip through JSON
    new_doc = DefinitionDocument._from_dict(**parsed)
    assert new_doc.to_dict() == doc.to_dict()


@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122).filter(str.isalnum), min_size=1),
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_flow_template_json_serialization(title, language, text):
    """FlowTemplate should be JSON serializable."""
    definition = DefinitionDocument(Language=language, Text=text)
    template = FlowTemplate(title, Definition=definition)
    
    json_str = template.to_json(validation=False)
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert "Type" in parsed
    assert parsed["Type"] == "AWS::IoTThingsGraph::FlowTemplate"
    assert "Properties" in parsed
    assert "Definition" in parsed["Properties"]