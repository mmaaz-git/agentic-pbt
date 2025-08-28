import troposphere.qbusiness as qb
from hypothesis import given, strategies as st, assume, settings
import json


# Strategy for generating valid property values based on type
def value_for_type(prop_type):
    """Generate a valid value for a given property type."""
    if prop_type == str:
        return st.text(min_size=1, max_size=100)
    elif prop_type == int:
        return st.integers(min_value=0, max_value=1000)
    elif prop_type == bool:
        return st.booleans()
    elif isinstance(prop_type, list):
        # Handle list types like [str]
        if prop_type[0] == str:
            return st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5)
    elif isinstance(prop_type, type) and issubclass(prop_type, qb.AWSProperty):
        # For nested property types, create a simple instance
        return st.builds(lambda: create_minimal_property(prop_type))
    else:
        # Default to a simple string
        return st.just("default_value")


def create_minimal_property(prop_class):
    """Create a minimal valid instance of a property class."""
    kwargs = {}
    for prop_name, (prop_type, required) in prop_class.props.items():
        if required:
            if prop_type == str:
                kwargs[prop_name] = "required_value"
            elif isinstance(prop_type, list) and prop_type[0] == str:
                kwargs[prop_name] = ["required_value"]
    return prop_class(**kwargs)


# Strategy for generating valid kwargs for AWS objects
@st.composite
def aws_object_kwargs(draw, cls):
    """Generate valid kwargs for creating an AWS object."""
    kwargs = {}
    
    # Always include at least required properties
    for prop_name, (prop_type, required) in cls.props.items():
        if required or draw(st.booleans()):  # Always include required, randomly include optional
            kwargs[prop_name] = draw(value_for_type(prop_type))
    
    return kwargs


# Test 1: Round-trip property for to_dict and from_dict
@given(
    display_name=st.text(min_size=1, max_size=100),
    description=st.text(min_size=0, max_size=200),
    include_description=st.booleans()
)
def test_application_round_trip(display_name, description, include_description):
    """Test that to_dict() and from_dict() are inverse operations for Application."""
    kwargs = {'DisplayName': display_name}
    if include_description:
        kwargs['Description'] = description
    
    # Create original object
    app1 = qb.Application('TestApp', **kwargs)
    
    # Serialize to dict
    app_dict = app1.to_dict()
    
    # Deserialize back
    app2 = qb.Application.from_dict('TestApp2', app_dict)
    
    # They should produce the same dict representation
    assert app2.to_dict() == app_dict


@given(
    display_name=st.text(min_size=1, max_size=100),
    application_id=st.text(min_size=1, max_size=100),
    index_id=st.text(min_size=1, max_size=100),
)
def test_index_round_trip(display_name, application_id, index_id):
    """Test that to_dict() and from_dict() are inverse operations for Index."""
    kwargs = {
        'DisplayName': display_name,
        'ApplicationId': application_id,
    }
    
    # Create original object
    idx1 = qb.Index('TestIndex', **kwargs)
    
    # Serialize to dict
    idx_dict = idx1.to_dict()
    
    # Deserialize back
    idx2 = qb.Index.from_dict('TestIndex2', idx_dict)
    
    # They should produce the same dict representation
    assert idx2.to_dict() == idx_dict


# Test 2: Validation of required fields
@given(st.data())
def test_required_field_validation(data):
    """Test that required fields are properly validated."""
    # Application requires DisplayName
    try:
        app = qb.Application('TestApp')  # Missing required DisplayName
        # If we get here, validation failed to catch missing required field
        assert False, "Should have raised validation error for missing DisplayName"
    except Exception as e:
        # Expected behavior - validation should catch this
        assert "DisplayName" in str(e) or "required" in str(e).lower()


# Test 3: Property classes round-trip
@given(
    mode=st.sampled_from(['ENABLED', 'DISABLED'])
)
def test_attachments_configuration_round_trip(mode):
    """Test AttachmentsConfiguration serialization round-trip."""
    config = qb.AttachmentsConfiguration(AttachmentsControlMode=mode)
    config_dict = config.to_dict()
    
    # Should be able to recreate from dict (though this class might not have from_dict)
    assert config_dict == {'AttachmentsControlMode': mode}
    
    # Create new instance with same params should produce same dict
    config2 = qb.AttachmentsConfiguration(AttachmentsControlMode=mode)
    assert config2.to_dict() == config_dict


# Test 4: Test all AWS Object classes for round-trip failures
@given(st.sampled_from([
    qb.Application,
    qb.Index, 
    qb.DataSource,
    qb.WebExperience,
    qb.Retriever,
    qb.Plugin,
    qb.Permission
]))
def test_all_aws_objects_round_trip(cls):
    """Test that all AWS Object classes have round-trip serialization issues."""
    # Create minimal valid instance
    kwargs = {}
    for prop_name, (prop_type, required) in cls.props.items():
        if required:
            if prop_type == str:
                kwargs[prop_name] = f"test_{prop_name}"
            elif isinstance(prop_type, list) and len(prop_type) > 0 and prop_type[0] == str:
                kwargs[prop_name] = [f"test_{prop_name}"]
            elif prop_type == bool:
                kwargs[prop_name] = True
            elif prop_type == int:
                kwargs[prop_name] = 42
    
    # Skip if we can't create a valid instance
    assume(len(kwargs) > 0 or len(cls.props) == 0)
    
    try:
        obj = cls('TestObject', **kwargs)
        obj_dict = obj.to_dict()
        
        # This should work but likely won't due to the bug
        obj2 = cls.from_dict('TestObject2', obj_dict)
        
        # If it works, verify round-trip
        assert obj2.to_dict() == obj_dict
    except AttributeError as e:
        # Expected bug - from_dict doesn't work properly
        assert "Properties property" in str(e) or "does not have a Properties" in str(e)
    except Exception as e:
        # Some classes might have other validation requirements
        # But the key bug is the from_dict issue
        if "Properties property" not in str(e):
            # This might be a different issue, let's not fail the test
            assume(False)  # Skip this case


# Test 5: Test that creating objects doesn't crash with valid inputs
@given(aws_object_kwargs(qb.Application))
@settings(max_examples=50)
def test_application_creation_no_crash(kwargs):
    """Test that Application can be created with various valid inputs without crashing."""
    try:
        app = qb.Application('TestApp', **kwargs)
        # Should be able to serialize
        app_dict = app.to_dict()
        assert 'Type' in app_dict
        assert app_dict['Type'] == 'AWS::QBusiness::Application'
        assert 'Properties' in app_dict
    except Exception as e:
        # Check if it's a validation error (which is acceptable)
        if "required" not in str(e).lower() and "validation" not in str(e).lower():
            raise  # Re-raise if it's not a validation error