import json
from hypothesis import given, strategies as st, settings, assume
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.appintegrations import (
    Application, ApplicationSourceConfig, ExternalUrlConfig,
    DataIntegration, FileConfiguration, ScheduleConfig,
    EventIntegration, EventFilter
)
from troposphere import Tags


# Strategy for generating valid URLs
valid_urls = st.text(min_size=1, max_size=100).map(lambda s: f"https://example.com/{s}")

# Strategy for valid strings (non-empty)
valid_strings = st.text(min_size=1, max_size=100)

# Strategy for folder paths
folder_paths = st.lists(
    st.text(min_size=1, max_size=50).map(lambda s: f"/path/{s}"),
    min_size=1,
    max_size=5
)


@given(
    access_url=valid_urls,
    approved_origins=st.lists(valid_urls, max_size=5)
)
def test_external_url_config_round_trip(access_url, approved_origins):
    """Test that ExternalUrlConfig survives to_dict/from_dict round trip"""
    original = ExternalUrlConfig(
        AccessUrl=access_url,
        ApprovedOrigins=approved_origins if approved_origins else None
    )
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    reconstructed = ExternalUrlConfig._from_dict(**dict_repr)
    
    # Should be equal
    assert original.to_dict() == reconstructed.to_dict()


@given(
    name=valid_strings,
    description=valid_strings,
    namespace=valid_strings,
    access_url=valid_urls,
    permissions=st.lists(valid_strings, max_size=3)
)
def test_application_required_fields(name, description, namespace, access_url, permissions):
    """Test that Application validates required fields"""
    # Create with all required fields
    app_source = ApplicationSourceConfig(
        ExternalUrlConfig=ExternalUrlConfig(AccessUrl=access_url)
    )
    
    app = Application(
        title="TestApp",
        Name=name,
        Description=description,
        Namespace=namespace,
        ApplicationSourceConfig=app_source,
        Permissions=permissions if permissions else None
    )
    
    # Should create dict without errors
    app_dict = app.to_dict()
    assert "Properties" in app_dict
    assert app_dict["Properties"]["Name"] == name


@given(
    name=valid_strings,
    kms_key=valid_strings,
    source_uri=valid_strings,
    description=st.one_of(st.none(), valid_strings),
    folders=folder_paths
)
def test_data_integration_validation(name, kms_key, source_uri, description, folders):
    """Test DataIntegration property validation"""
    # Create with required fields
    di = DataIntegration(
        title="TestDI",
        Name=name,
        KmsKey=kms_key,
        SourceURI=source_uri,
        Description=description
    )
    
    # Add optional FileConfiguration
    if folders:
        di.FileConfiguration = FileConfiguration(Folders=folders)
    
    # Should validate and convert to dict
    di_dict = di.to_dict()
    assert di_dict["Type"] == "AWS::AppIntegrations::DataIntegration"
    assert di_dict["Properties"]["Name"] == name


@given(
    schedule_expr=st.text(min_size=1, max_size=100),
    first_exec=st.one_of(st.none(), valid_strings),
    object_name=st.one_of(st.none(), valid_strings)
)
def test_schedule_config_properties(schedule_expr, first_exec, object_name):
    """Test ScheduleConfig handles optional properties correctly"""
    sc = ScheduleConfig(
        ScheduleExpression=schedule_expr,
        FirstExecutionFrom=first_exec,
        Object=object_name
    )
    
    sc_dict = sc.to_dict()
    assert sc_dict["ScheduleExpression"] == schedule_expr
    
    # Optional fields should only appear if provided
    if first_exec:
        assert sc_dict.get("FirstExecutionFrom") == first_exec
    else:
        assert "FirstExecutionFrom" not in sc_dict or sc_dict["FirstExecutionFrom"] is None


@given(
    name=valid_strings,
    event_bus=valid_strings,
    source=valid_strings,
    description=st.one_of(st.none(), valid_strings)
)
def test_event_integration_complete(name, event_bus, source, description):
    """Test EventIntegration with all fields"""
    ef = EventFilter(Source=source)
    ei = EventIntegration(
        title="TestEvent",
        Name=name,
        EventBridgeBus=event_bus,
        EventFilter=ef,
        Description=description
    )
    
    ei_dict = ei.to_dict()
    assert ei_dict["Type"] == "AWS::AppIntegrations::EventIntegration"
    assert ei_dict["Properties"]["Name"] == name
    assert ei_dict["Properties"]["EventFilter"]["Source"] == source


@given(
    access_url1=valid_urls,
    access_url2=valid_urls
)
def test_equality_property(access_url1, access_url2):
    """Test that identical objects are equal"""
    # Create two identical objects
    obj1 = ExternalUrlConfig(AccessUrl=access_url1)
    obj2 = ExternalUrlConfig(AccessUrl=access_url1)
    
    # Should be equal if same properties
    assert (obj1 == obj2) == (access_url1 == access_url1)
    
    # Different properties should not be equal
    obj3 = ExternalUrlConfig(AccessUrl=access_url2)
    if access_url1 != access_url2:
        assert obj1 != obj3


@given(
    name=valid_strings,
    description=valid_strings,
    namespace=valid_strings,
    access_url=valid_urls
)
def test_json_serialization_validity(name, description, namespace, access_url):
    """Test that to_json produces valid JSON"""
    app_source = ApplicationSourceConfig(
        ExternalUrlConfig=ExternalUrlConfig(AccessUrl=access_url)
    )
    
    app = Application(
        title="TestApp",
        Name=name,
        Description=description,
        Namespace=namespace,
        ApplicationSourceConfig=app_source
    )
    
    # to_json should produce valid JSON
    json_str = app.to_json()
    
    # Should be parseable
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    assert "Properties" in parsed
    
    # Properties should match
    assert parsed["Properties"]["Name"] == name
    assert parsed["Properties"]["Description"] == description


@given(st.data())
def test_missing_required_fields_raise_error(data):
    """Test that missing required fields raise ValueError"""
    # Try creating Application without required fields
    try:
        app = Application(title="TestApp")
        # Calling to_dict() should trigger validation
        app.to_dict()
        # Should not reach here
        assert False, "Expected ValueError for missing required fields"
    except ValueError as e:
        # Expected - missing required fields
        assert "required" in str(e).lower()


@given(
    folders=folder_paths,
    filters=st.one_of(st.none(), st.dictionaries(valid_strings, valid_strings, max_size=3))
)
def test_file_configuration_dict_filters(folders, filters):
    """Test FileConfiguration handles dict filters correctly"""
    fc = FileConfiguration(
        Folders=folders,
        Filters=filters
    )
    
    fc_dict = fc.to_dict()
    assert fc_dict["Folders"] == folders
    
    if filters:
        assert fc_dict.get("Filters") == filters


@given(
    tag_key=valid_strings,
    tag_value=valid_strings
)  
def test_tags_property(tag_key, tag_value):
    """Test that Tags work correctly with AWS objects"""
    assume(tag_key != tag_value)  # Make keys and values different for clarity
    
    tags = Tags({tag_key: tag_value})
    
    # Create an object with tags
    app_source = ApplicationSourceConfig(
        ExternalUrlConfig=ExternalUrlConfig(AccessUrl="https://example.com")
    )
    
    app = Application(
        title="TestApp",
        Name="TestName",
        Description="TestDesc",
        Namespace="TestNS",
        ApplicationSourceConfig=app_source,
        Tags=tags
    )
    
    app_dict = app.to_dict()
    # Tags should be in the dict
    assert "Tags" in app_dict["Properties"]