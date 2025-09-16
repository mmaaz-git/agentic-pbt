"""
Property-based tests for troposphere.voiceid module
"""
import json
from hypothesis import given, strategies as st, assume
import troposphere.voiceid as voiceid
from troposphere import Tags


# Strategy for valid KMS key IDs
kms_key_strategy = st.one_of(
    st.text(min_size=1, max_size=100),  # Simple key ID
    st.from_regex(r"arn:aws:kms:[a-z0-9-]+:\d{12}:key/[a-f0-9-]{36}", fullmatch=True),  # ARN format
)

# Strategy for valid names
name_strategy = st.text(min_size=1, max_size=200).filter(lambda x: x.strip())

# Strategy for descriptions
description_strategy = st.text(min_size=0, max_size=500)

# Strategy for tags
tag_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    values=st.text(min_size=0, max_size=100),
    min_size=0,
    max_size=10
)


@given(
    title=name_strategy,
    name=name_strategy,
    description=st.one_of(st.none(), description_strategy),
    kms_key_id=kms_key_strategy,
    tags=st.one_of(st.none(), tag_strategy)
)
def test_round_trip_property(title, name, description, kms_key_id, tags):
    """Test that from_dict(to_dict()) preserves all data"""
    # Create a Domain object
    domain_kwargs = {
        'Name': name,
        'ServerSideEncryptionConfiguration': voiceid.ServerSideEncryptionConfiguration(
            KmsKeyId=kms_key_id
        )
    }
    
    if description is not None:
        domain_kwargs['Description'] = description
    
    if tags is not None:
        domain_kwargs['Tags'] = Tags(**tags)
    
    domain1 = voiceid.Domain(title, **domain_kwargs)
    
    # Convert to dict
    dict1 = domain1.to_dict()
    
    # Recreate from dict
    props = dict1.get('Properties', {})
    domain2 = voiceid.Domain.from_dict(title, props)
    
    # Convert back to dict
    dict2 = domain2.to_dict()
    
    # They should be equal
    assert dict1 == dict2, f"Round-trip failed: {dict1} != {dict2}"


@given(
    title=name_strategy,
    name=name_strategy,
    kms_key_id=kms_key_strategy
)
def test_json_serialization(title, name, kms_key_id):
    """Test that to_json produces valid JSON that can be parsed"""
    domain = voiceid.Domain(
        title,
        Name=name,
        ServerSideEncryptionConfiguration=voiceid.ServerSideEncryptionConfiguration(
            KmsKeyId=kms_key_id
        )
    )
    
    # Get JSON string
    json_str = domain.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should contain expected structure
    assert 'Type' in parsed
    assert parsed['Type'] == 'AWS::VoiceID::Domain'
    assert 'Properties' in parsed
    assert 'Name' in parsed['Properties']
    assert parsed['Properties']['Name'] == name


@given(
    title=name_strategy,
    name=name_strategy,
    kms_key_id=kms_key_strategy
)
def test_to_dict_idempotent(title, name, kms_key_id):
    """Test that calling to_dict multiple times gives same result"""
    domain = voiceid.Domain(
        title,
        Name=name,
        ServerSideEncryptionConfiguration=voiceid.ServerSideEncryptionConfiguration(
            KmsKeyId=kms_key_id
        )
    )
    
    dict1 = domain.to_dict()
    dict2 = domain.to_dict()
    dict3 = domain.to_dict()
    
    assert dict1 == dict2 == dict3


@given(
    title=name_strategy,
    invalid_name=st.one_of(
        st.integers(),
        st.floats(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_type_validation_name(title, invalid_name):
    """Test that invalid types for Name are caught"""
    try:
        domain = voiceid.Domain(
            title,
            Name=invalid_name,
            ServerSideEncryptionConfiguration=voiceid.ServerSideEncryptionConfiguration(
                KmsKeyId='test-key'
            )
        )
        # Should fail during to_dict with validation
        domain.to_dict()
        assert False, f"Expected type error for Name={invalid_name}"
    except TypeError as e:
        # Expected - type checking should catch this
        assert "expected <class 'str'>" in str(e)


@given(
    title=name_strategy,
    name=name_strategy,
    invalid_sse=st.one_of(
        st.text(),
        st.integers(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_type_validation_sse(title, name, invalid_sse):
    """Test that invalid types for ServerSideEncryptionConfiguration are caught"""
    try:
        domain = voiceid.Domain(
            title,
            Name=name,
            ServerSideEncryptionConfiguration=invalid_sse
        )
        # Should fail during to_dict with validation
        domain.to_dict()
        assert False, f"Expected type error for ServerSideEncryptionConfiguration={invalid_sse}"
    except (TypeError, AttributeError) as e:
        # Expected - type checking should catch this
        pass


@given(title=name_strategy)
def test_missing_required_fields_validation(title):
    """Test that missing required fields are caught by validation"""
    # Create domain without required fields
    domain = voiceid.Domain(title)
    
    try:
        # Should fail with validation=True (default)
        domain.to_dict()
        assert False, "Expected validation error for missing required fields"
    except ValueError as e:
        assert "Name required" in str(e)
    
    # Should succeed with validation=False
    result = domain.to_dict(validation=False)
    assert result['Type'] == 'AWS::VoiceID::Domain'


@given(
    kms_key_id=kms_key_strategy
)
def test_serverside_encryption_configuration(kms_key_id):
    """Test ServerSideEncryptionConfiguration to_dict"""
    sse = voiceid.ServerSideEncryptionConfiguration(KmsKeyId=kms_key_id)
    result = sse.to_dict()
    
    assert result == {'KmsKeyId': kms_key_id}


@given(
    title1=name_strategy,
    title2=name_strategy,
    name=name_strategy,
    kms_key_id=kms_key_strategy
)
def test_title_independence(title1, title2, name, kms_key_id):
    """Test that title doesn't affect the Properties in to_dict"""
    assume(title1 != title2)
    
    domain1 = voiceid.Domain(
        title1,
        Name=name,
        ServerSideEncryptionConfiguration=voiceid.ServerSideEncryptionConfiguration(
            KmsKeyId=kms_key_id
        )
    )
    
    domain2 = voiceid.Domain(
        title2,
        Name=name,
        ServerSideEncryptionConfiguration=voiceid.ServerSideEncryptionConfiguration(
            KmsKeyId=kms_key_id
        )
    )
    
    dict1 = domain1.to_dict()
    dict2 = domain2.to_dict()
    
    # Properties should be the same regardless of title
    assert dict1['Properties'] == dict2['Properties']