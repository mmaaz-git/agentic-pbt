import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.robomaker as robomaker


# Strategy for valid AWS names (simplified but reasonable)
aws_name_strategy = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='"\\'),
    min_size=1,
    max_size=255
).filter(lambda x: not x.startswith(' ') and not x.endswith(' '))

# Strategy for version strings
version_strategy = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='"\\'),
    min_size=1,
    max_size=50
)

# Strategy for S3 bucket names (AWS constraints)
s3_bucket_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters=".-"),
    min_size=3,
    max_size=63
).filter(lambda x: not x.startswith('.') and not x.endswith('.') and '..' not in x)

# Strategy for S3 keys
s3_key_strategy = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='"\\'),
    min_size=1,
    max_size=1024
)

# Strategy for architecture values
architecture_strategy = st.sampled_from(['X86_64', 'ARM64', 'ARMHF'])


@given(
    name=aws_name_strategy,
    version=st.one_of(st.none(), version_strategy)
)
def test_robot_software_suite_round_trip(name, version):
    """Test that RobotSoftwareSuite survives to_dict/from_dict round-trip"""
    # Create object
    kwargs = {'Name': name}
    if version is not None:
        kwargs['Version'] = version
    
    original = robomaker.RobotSoftwareSuite(**kwargs)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    reconstructed = robomaker.RobotSoftwareSuite.from_dict('TestSuite', dict_repr)
    
    # Check round-trip property
    assert dict_repr == reconstructed.to_dict()


@given(
    name=aws_name_strategy,
    version=st.one_of(st.none(), version_strategy)
)
def test_simulation_software_suite_json_serialization(name, version):
    """Test that SimulationSoftwareSuite JSON serialization is consistent"""
    kwargs = {'Name': name}
    if version is not None:
        kwargs['Version'] = version
    
    suite = robomaker.SimulationSoftwareSuite(**kwargs)
    
    # Test JSON serialization
    json_str = suite.to_json()
    dict_repr = suite.to_dict()
    
    # JSON should be valid and match dict representation
    parsed_json = json.loads(json_str)
    assert parsed_json == dict_repr


@given(
    name=aws_name_strategy,
    version=version_strategy
)
def test_rendering_engine_required_fields(name, version):
    """Test that RenderingEngine enforces required fields"""
    # Both Name and Version are required for RenderingEngine
    engine = robomaker.RenderingEngine(Name=name, Version=version)
    
    # Should be able to validate without errors
    engine.validate()
    
    # Should serialize correctly
    dict_repr = engine.to_dict()
    assert 'Name' in dict_repr
    assert 'Version' in dict_repr
    assert dict_repr['Name'] == name
    assert dict_repr['Version'] == version


@given(
    architecture=architecture_strategy,
    s3_bucket=s3_bucket_strategy,
    s3_key=s3_key_strategy
)
def test_source_config_round_trip(architecture, s3_bucket, s3_key):
    """Test SourceConfig round-trip property"""
    source = robomaker.SourceConfig(
        Architecture=architecture,
        S3Bucket=s3_bucket,
        S3Key=s3_key
    )
    
    dict_repr = source.to_dict()
    reconstructed = robomaker.SourceConfig.from_dict('TestSource', dict_repr)
    
    assert dict_repr == reconstructed.to_dict()


@given(
    app_name=st.one_of(st.none(), aws_name_strategy),
    robot_name=aws_name_strategy,
    robot_version=st.one_of(st.none(), version_strategy),
    sim_name=aws_name_strategy,
    sim_version=st.one_of(st.none(), version_strategy),
    render_name=st.one_of(st.none(), aws_name_strategy),
    render_version=st.one_of(st.none(), version_strategy),
    include_rendering=st.booleans()
)
@settings(max_examples=100)
def test_simulation_application_complex_serialization(
    app_name, robot_name, robot_version, sim_name, sim_version,
    render_name, render_version, include_rendering
):
    """Test SimulationApplication with nested objects"""
    # Build robot software suite
    robot_kwargs = {'Name': robot_name}
    if robot_version:
        robot_kwargs['Version'] = robot_version
    robot_suite = robomaker.RobotSoftwareSuite(**robot_kwargs)
    
    # Build simulation software suite  
    sim_kwargs = {'Name': sim_name}
    if sim_version:
        sim_kwargs['Version'] = sim_version
    sim_suite = robomaker.SimulationSoftwareSuite(**sim_kwargs)
    
    # Build kwargs for SimulationApplication
    app_kwargs = {
        'RobotSoftwareSuite': robot_suite,
        'SimulationSoftwareSuite': sim_suite
    }
    
    if app_name:
        app_kwargs['Name'] = app_name
    
    # Optionally add rendering engine
    if include_rendering and render_name and render_version:
        rendering = robomaker.RenderingEngine(Name=render_name, Version=render_version)
        app_kwargs['RenderingEngine'] = rendering
    
    # Create application
    app = robomaker.SimulationApplication(**app_kwargs)
    
    # Test serialization
    dict_repr = app.to_dict()
    json_str = app.to_json()
    
    # Verify nested objects are properly serialized
    assert 'RobotSoftwareSuite' in dict_repr
    assert dict_repr['RobotSoftwareSuite']['Name'] == robot_name
    
    assert 'SimulationSoftwareSuite' in dict_repr
    assert dict_repr['SimulationSoftwareSuite']['Name'] == sim_name
    
    if include_rendering and render_name and render_version:
        assert 'RenderingEngine' in dict_repr
        assert dict_repr['RenderingEngine']['Name'] == render_name
        assert dict_repr['RenderingEngine']['Version'] == render_version
    
    # JSON should be valid
    parsed = json.loads(json_str)
    assert parsed == dict_repr


@given(
    architecture=architecture_strategy,
    greengrass_id=aws_name_strategy,
    name=st.one_of(st.none(), aws_name_strategy),
    fleet=st.one_of(st.none(), aws_name_strategy)
)
def test_robot_validation_and_serialization(architecture, greengrass_id, name, fleet):
    """Test Robot class with required and optional fields"""
    kwargs = {
        'Architecture': architecture,
        'GreengrassGroupId': greengrass_id
    }
    
    if name:
        kwargs['Name'] = name
    if fleet:
        kwargs['Fleet'] = fleet
    
    robot = robomaker.Robot(**kwargs)
    
    # Should validate
    robot.validate()
    
    # Should serialize correctly
    dict_repr = robot.to_dict()
    assert dict_repr['Architecture'] == architecture
    assert dict_repr['GreengrassGroupId'] == greengrass_id
    
    # Test round-trip
    reconstructed = robomaker.Robot.from_dict('TestRobot', dict_repr)
    assert dict_repr == reconstructed.to_dict()


@given(
    application=aws_name_strategy,
    current_revision=st.one_of(st.none(), aws_name_strategy)
)
def test_robot_application_version_properties(application, current_revision):
    """Test RobotApplicationVersion properties"""
    kwargs = {'Application': application}
    if current_revision:
        kwargs['CurrentRevisionId'] = current_revision
    
    version = robomaker.RobotApplicationVersion(**kwargs)
    
    # Test serialization
    dict_repr = version.to_dict()
    assert dict_repr['Application'] == application
    
    if current_revision:
        assert dict_repr['CurrentRevisionId'] == current_revision
    
    # Test JSON
    json_str = version.to_json()
    parsed = json.loads(json_str)
    assert parsed == dict_repr
    
    # Test round-trip
    reconstructed = robomaker.RobotApplicationVersion.from_dict('TestVersion', dict_repr)
    assert dict_repr == reconstructed.to_dict()


@given(st.data())
def test_from_dict_preserves_all_fields(data):
    """Test that from_dict preserves all valid fields for various classes"""
    # Generate random valid data for RobotApplication
    robot_suite = robomaker.RobotSoftwareSuite(
        Name=data.draw(aws_name_strategy),
        Version=data.draw(st.one_of(st.none(), version_strategy))
    )
    
    app_kwargs = {'RobotSoftwareSuite': robot_suite}
    
    # Add optional fields randomly
    if data.draw(st.booleans()):
        app_kwargs['Name'] = data.draw(aws_name_strategy)
    if data.draw(st.booleans()):
        app_kwargs['CurrentRevisionId'] = data.draw(aws_name_strategy)
    if data.draw(st.booleans()):
        app_kwargs['Environment'] = data.draw(aws_name_strategy)
    
    original = robomaker.RobotApplication(**app_kwargs)
    dict_repr = original.to_dict()
    
    # Reconstruct and verify all fields preserved
    reconstructed = robomaker.RobotApplication.from_dict('TestApp', dict_repr)
    new_dict = reconstructed.to_dict()
    
    # All original fields should be preserved
    for key, value in dict_repr.items():
        assert key in new_dict
        assert new_dict[key] == value


@given(
    name=st.one_of(st.none(), aws_name_strategy),
    tags=st.one_of(
        st.none(),
        st.dictionaries(
            keys=aws_name_strategy,
            values=aws_name_strategy,
            min_size=0,
            max_size=5
        )
    )
)
def test_fleet_with_tags(name, tags):
    """Test Fleet class with optional tags"""
    kwargs = {}
    if name:
        kwargs['Name'] = name
    if tags:
        kwargs['Tags'] = tags
    
    fleet = robomaker.Fleet(**kwargs)
    
    # Should validate
    fleet.validate()
    
    # Should serialize correctly
    dict_repr = fleet.to_dict()
    
    if name:
        assert dict_repr['Name'] == name
    if tags:
        assert dict_repr['Tags'] == tags
    
    # Test JSON serialization
    json_str = fleet.to_json()
    parsed = json.loads(json_str)
    assert parsed == dict_repr