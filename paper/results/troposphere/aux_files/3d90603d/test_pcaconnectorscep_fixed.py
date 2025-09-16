import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.pcaconnectorscep as pcaconnectorscep


# Strategies for generating valid input data
# CloudFormation logical IDs must be ASCII alphanumeric only
valid_title_strategy = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=50)
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
    title=valid_title_strategy,
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


# Test 2: Error message precision for non-ASCII characters
def test_error_message_precision():
    """The error message should be clear about ASCII requirement"""
    try:
        # µ is alphanumeric in Unicode sense but not ASCII
        challenge = pcaconnectorscep.Challenge("µ", ConnectorArn="arn:test")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        # The error says "not alphanumeric" but µ IS alphanumeric (just not ASCII)
        # This is misleading - it should say "not ASCII alphanumeric" 
        error_msg = str(e)
        assert "not alphanumeric" in error_msg
        # Demonstrate that the character IS alphanumeric in Unicode
        assert "µ".isalnum() == True  # µ is alphanumeric in Unicode
        print(f"Bug: Error message '{error_msg}' is misleading")
        print(f"The character 'µ' IS alphanumeric (µ.isalnum()={repr('µ'.isalnum())})")
        print("The error should say 'not ASCII alphanumeric' for clarity")


# Test 3: Empty title validation
@given(empty_str=st.just(""))
def test_empty_title_validation(empty_str):
    """Empty strings should be rejected as titles"""
    try:
        challenge = pcaconnectorscep.Challenge(empty_str, ConnectorArn="arn:test")
        challenge.to_dict()
        assert False, "Should have raised ValueError for empty title"
    except ValueError as e:
        assert "not alphanumeric" in str(e) or "Name" in str(e)


# Test 4: Special characters in title
@given(
    special_char=st.sampled_from(["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "+", "=", " ", ".", ","])
)
def test_special_chars_in_title(special_char):
    """Special characters should be rejected in titles"""
    title = f"Test{special_char}Name"
    try:
        challenge = pcaconnectorscep.Challenge(title, ConnectorArn="arn:test")
        assert False, f"Should have raised ValueError for title with '{special_char}'"
    except ValueError as e:
        assert "not alphanumeric" in str(e)


# Test 5: Connector with all features
@given(
    title=valid_title_strategy,
    ca_arn=valid_arn_strategy,
    azure_app_id=valid_string_strategy,
    domain=valid_string_strategy,
    tags=st.one_of(st.none(), tags_strategy)
)
def test_connector_full_features(title, ca_arn, azure_app_id, domain, tags):
    # Create with all features
    intune_config = pcaconnectorscep.IntuneConfiguration(
        AzureApplicationId=azure_app_id,
        Domain=domain
    )
    mdm = pcaconnectorscep.MobileDeviceManagement(Intune=intune_config)
    
    kwargs = {
        "CertificateAuthorityArn": ca_arn,
        "MobileDeviceManagement": mdm
    }
    if tags is not None:
        kwargs["Tags"] = tags
    
    connector = pcaconnectorscep.Connector(title, **kwargs)
    
    # Serialize and check
    connector_dict = connector.to_dict()
    assert "Properties" in connector_dict
    assert "CertificateAuthorityArn" in connector_dict["Properties"]
    assert "MobileDeviceManagement" in connector_dict["Properties"]
    
    # Check nested structure preserved
    mdm_dict = connector_dict["Properties"]["MobileDeviceManagement"]
    assert "Intune" in mdm_dict
    assert mdm_dict["Intune"]["AzureApplicationId"] == azure_app_id
    assert mdm_dict["Intune"]["Domain"] == domain


# Test 6: Property assignment and retrieval
@given(
    title=valid_title_strategy,
    arn1=valid_arn_strategy,
    arn2=valid_arn_strategy
)
def test_property_mutation(title, arn1, arn2):
    """Test that properties can be changed after creation"""
    assume(arn1 != arn2)  # Make sure we're actually changing the value
    
    challenge = pcaconnectorscep.Challenge(title, ConnectorArn=arn1)
    
    # Check initial value
    assert challenge.ConnectorArn == arn1
    
    # Change the value
    challenge.ConnectorArn = arn2
    
    # Check new value
    assert challenge.ConnectorArn == arn2
    
    # Verify it serializes with new value
    challenge_dict = challenge.to_dict()
    assert challenge_dict["Properties"]["ConnectorArn"] == arn2


# Test 7: None vs missing optional properties
def test_none_vs_missing_properties():
    """Test difference between None and missing optional properties"""
    # Create with no Tags
    conn1 = pcaconnectorscep.Connector("Test1", CertificateAuthorityArn="arn:test")
    dict1 = conn1.to_dict()
    
    # Create with Tags=None - should be same as omitting it
    conn2 = pcaconnectorscep.Connector("Test2", CertificateAuthorityArn="arn:test", Tags=None)
    dict2 = conn2.to_dict()
    
    # Both should not have Tags in the output
    assert "Tags" not in dict1["Properties"]
    assert "Tags" not in dict2["Properties"]


# Test 8: Large tag dictionaries
@given(
    title=valid_title_strategy,
    large_tags=st.dictionaries(
        keys=st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=128),
        values=st.text(min_size=0, max_size=256),
        min_size=50,
        max_size=100
    )
)
@settings(max_examples=10)  # Reduce number since these are large
def test_large_tag_dictionaries(title, large_tags):
    """Test with large tag dictionaries"""
    challenge = pcaconnectorscep.Challenge(title, ConnectorArn="arn:test", Tags=large_tags)
    
    # Should serialize without issues
    challenge_dict = challenge.to_dict()
    assert challenge_dict["Properties"]["Tags"] == large_tags
    
    # Round trip
    reconstructed = pcaconnectorscep.Challenge.from_dict(title, challenge_dict["Properties"])
    assert reconstructed.Tags == large_tags