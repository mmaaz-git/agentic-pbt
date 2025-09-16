import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.pcaconnectorscep as pcaconnectorscep


# Strategies for generating valid input data
valid_arn_strategy = st.text(min_size=1, max_size=256).filter(lambda x: x.strip() != "")
valid_string_strategy = st.text(min_size=1, max_size=256).filter(lambda x: x.strip() != "")
tags_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=128).filter(lambda x: x.strip() != ""),
    values=st.text(min_size=0, max_size=256),
    min_size=0,
    max_size=10
)


# Test 1: Round-trip serialization for Challenge
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
    connector_arn=valid_arn_strategy,
    tags=st.one_of(st.none(), tags_strategy)
)
def test_challenge_round_trip(title, connector_arn, tags):
    # Create Challenge object
    kwargs = {"ConnectorArn": connector_arn}
    if tags is not None:
        kwargs["Tags"] = tags
    
    challenge = pcaconnectorscep.Challenge(title, **kwargs)
    
    # Convert to dict
    challenge_dict = challenge.to_dict()
    
    # Verify we can create from dict
    reconstructed = pcaconnectorscep.Challenge.from_dict(title, challenge_dict["Properties"])
    
    # Check equality
    assert challenge.title == reconstructed.title
    assert challenge.to_dict() == reconstructed.to_dict()


# Test 2: Round-trip serialization for IntuneConfiguration
@given(
    azure_app_id=valid_string_strategy,
    domain=valid_string_strategy
)
def test_intune_configuration_round_trip(azure_app_id, domain):
    config = pcaconnectorscep.IntuneConfiguration(
        AzureApplicationId=azure_app_id,
        Domain=domain
    )
    
    # Convert to dict
    config_dict = config.to_dict()
    
    # Create from dict
    reconstructed = pcaconnectorscep.IntuneConfiguration._from_dict(**config_dict)
    
    # Check equality
    assert config.to_dict() == reconstructed.to_dict()


# Test 3: Round-trip for Connector with nested properties
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
    ca_arn=valid_arn_strategy,
    azure_app_id=valid_string_strategy,
    domain=valid_string_strategy,
    include_mdm=st.booleans(),
    tags=st.one_of(st.none(), tags_strategy)
)
def test_connector_round_trip_with_nested(title, ca_arn, azure_app_id, domain, include_mdm, tags):
    kwargs = {"CertificateAuthorityArn": ca_arn}
    
    if include_mdm:
        intune_config = pcaconnectorscep.IntuneConfiguration(
            AzureApplicationId=azure_app_id,
            Domain=domain
        )
        mdm = pcaconnectorscep.MobileDeviceManagement(Intune=intune_config)
        kwargs["MobileDeviceManagement"] = mdm
    
    if tags is not None:
        kwargs["Tags"] = tags
    
    connector = pcaconnectorscep.Connector(title, **kwargs)
    
    # Convert to dict
    connector_dict = connector.to_dict()
    
    # Create from dict
    reconstructed = pcaconnectorscep.Connector.from_dict(title, connector_dict["Properties"])
    
    # Check equality
    assert connector.title == reconstructed.title
    assert connector.to_dict() == reconstructed.to_dict()


# Test 4: Required field validation for Challenge
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50)
)
def test_challenge_required_fields(title):
    # Should fail without ConnectorArn
    challenge = pcaconnectorscep.Challenge(title)
    
    try:
        # This should raise ValueError for missing required field
        challenge.to_dict()
        assert False, "Expected ValueError for missing ConnectorArn"
    except ValueError as e:
        assert "ConnectorArn" in str(e)
        assert "required" in str(e).lower()


# Test 5: Required field validation for IntuneConfiguration
def test_intune_configuration_required_fields():
    # Missing AzureApplicationId
    config1 = pcaconnectorscep.IntuneConfiguration(Domain="example.com")
    try:
        config1.to_dict()
        assert False, "Expected ValueError for missing AzureApplicationId"
    except ValueError as e:
        assert "AzureApplicationId" in str(e)
    
    # Missing Domain
    config2 = pcaconnectorscep.IntuneConfiguration(AzureApplicationId="app-id")
    try:
        config2.to_dict()
        assert False, "Expected ValueError for missing Domain"
    except ValueError as e:
        assert "Domain" in str(e)


# Test 6: Type validation
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
    invalid_value=st.one_of(st.integers(), st.floats(), st.lists(st.text()))
)
def test_challenge_type_validation(title, invalid_value):
    # Try to set ConnectorArn with non-string value
    try:
        challenge = pcaconnectorscep.Challenge(title, ConnectorArn=invalid_value)
        # The type checking happens during to_dict() validation
        challenge.to_dict()
        # If we got here without error, check if the value was coerced to string
        if not isinstance(invalid_value, str):
            assert False, f"Expected type error for ConnectorArn={invalid_value}"
    except (TypeError, ValueError):
        # Expected behavior for invalid types
        pass


# Test 7: Equality properties
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
    connector_arn=valid_arn_strategy,
    tags=st.one_of(st.none(), tags_strategy)
)
def test_challenge_equality(title, connector_arn, tags):
    kwargs = {"ConnectorArn": connector_arn}
    if tags is not None:
        kwargs["Tags"] = tags
    
    # Create two identical challenges
    challenge1 = pcaconnectorscep.Challenge(title, **kwargs)
    challenge2 = pcaconnectorscep.Challenge(title, **kwargs)
    
    # They should be equal
    assert challenge1 == challenge2
    assert not (challenge1 != challenge2)
    
    # Hash should be same for equal objects
    assert hash(challenge1) == hash(challenge2)


# Test 8: JSON serialization round-trip
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
    connector_arn=valid_arn_strategy
)
def test_challenge_json_serialization(title, connector_arn):
    challenge = pcaconnectorscep.Challenge(title, ConnectorArn=connector_arn)
    
    # Convert to JSON
    json_str = challenge.to_json()
    
    # Parse JSON
    parsed = json.loads(json_str)
    
    # Should be able to recreate from parsed data
    reconstructed = pcaconnectorscep.Challenge.from_dict(title, parsed["Properties"])
    
    # Should be equal
    assert challenge.to_dict() == reconstructed.to_dict()


# Test 9: OpenIdConfiguration with all optional fields
@given(
    audience=st.one_of(st.none(), valid_string_strategy),
    issuer=st.one_of(st.none(), valid_string_strategy),
    subject=st.one_of(st.none(), valid_string_strategy)
)
def test_openid_configuration_optional_fields(audience, issuer, subject):
    kwargs = {}
    if audience is not None:
        kwargs["Audience"] = audience
    if issuer is not None:
        kwargs["Issuer"] = issuer
    if subject is not None:
        kwargs["Subject"] = subject
    
    config = pcaconnectorscep.OpenIdConfiguration(**kwargs)
    
    # Should be able to convert to dict without required fields
    config_dict = config.to_dict()
    
    # Recreate from dict
    if config_dict:  # Only if there are properties
        reconstructed = pcaconnectorscep.OpenIdConfiguration._from_dict(**config_dict)
        assert config.to_dict() == reconstructed.to_dict()


# Test 10: Setting invalid attribute names
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
    attr_name=st.text(min_size=1, max_size=50).filter(lambda x: x not in ["ConnectorArn", "Tags", "title"])
)
def test_challenge_invalid_attribute(title, attr_name):
    challenge = pcaconnectorscep.Challenge(title, ConnectorArn="arn:test")
    
    # Try to set an invalid attribute
    try:
        setattr(challenge, attr_name, "some_value")
        # If it didn't raise an error, check if it's actually set
        if not hasattr(challenge, attr_name):
            assert False, f"Attribute {attr_name} was not set but no error was raised"
    except AttributeError as e:
        # Expected behavior - invalid attributes should raise AttributeError
        assert "does not support attribute" in str(e)