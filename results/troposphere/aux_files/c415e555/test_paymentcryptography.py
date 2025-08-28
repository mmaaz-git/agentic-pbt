"""Property-based tests for troposphere.paymentcryptography module."""

import json
from hypothesis import given, strategies as st, assume, settings
from troposphere.paymentcryptography import (
    Alias, Key, KeyAttributes, KeyModesOfUse
)
from troposphere import validators, Tags
import pytest


# Strategy for valid boolean inputs
valid_boolean_inputs = st.sampled_from([
    True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'
])

# Strategy for invalid boolean inputs
invalid_boolean_inputs = st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ['1', '0', 'true', 'false', 'True', 'False', '']),
    st.none(),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
)


@given(valid_boolean_inputs)
def test_boolean_validator_idempotence(value):
    """Test that boolean validator is idempotent for valid inputs."""
    first_result = validators.boolean(value)
    second_result = validators.boolean(first_result)
    assert first_result == second_result
    assert isinstance(first_result, bool)
    assert isinstance(second_result, bool)


@given(invalid_boolean_inputs)
def test_boolean_validator_rejects_invalid(value):
    """Test that boolean validator rejects invalid inputs."""
    with pytest.raises(ValueError):
        validators.boolean(value)


@given(
    decrypt=st.booleans(),
    derive_key=st.booleans(), 
    encrypt=st.booleans(),
    generate=st.booleans(),
    no_restrictions=st.booleans(),
    sign=st.booleans(),
    unwrap=st.booleans(),
    verify=st.booleans(),
    wrap=st.booleans()
)
def test_key_modes_of_use_round_trip(
    decrypt, derive_key, encrypt, generate, no_restrictions,
    sign, unwrap, verify, wrap
):
    """Test round-trip serialization for KeyModesOfUse."""
    original = KeyModesOfUse(
        Decrypt=decrypt,
        DeriveKey=derive_key,
        Encrypt=encrypt,
        Generate=generate,
        NoRestrictions=no_restrictions,
        Sign=sign,
        Unwrap=unwrap,
        Verify=verify,
        Wrap=wrap
    )
    
    # Serialize to dict
    dict_repr = original.to_dict()
    
    # Deserialize back
    restored = KeyModesOfUse.from_dict(None, dict_repr)
    
    # Should be equal
    assert original.to_dict() == restored.to_dict()
    assert original == restored


@given(st.text(min_size=1))
def test_alias_name_type_validation(name_value):
    """Test that Alias validates AliasName as string."""
    # String should work
    alias = Alias('TestAlias', AliasName=name_value)
    result = alias.to_dict()
    assert result['Properties']['AliasName'] == name_value
    
    # Non-string should fail
    if not isinstance(name_value, str):
        with pytest.raises(TypeError):
            Alias('TestAlias', AliasName=123)


@given(st.text())
def test_alias_title_validation(title):
    """Test that Alias title must be alphanumeric."""
    # Check if title is valid (alphanumeric only)
    is_valid = title and all(c.isalnum() for c in title)
    
    if is_valid:
        alias = Alias(title, AliasName='test')
        assert alias.title == title
    else:
        with pytest.raises(ValueError, match=r'Name .* not alphanumeric'):
            Alias(title, AliasName='test')


@given(
    key_algorithm=st.text(min_size=1),
    key_class=st.text(min_size=1),
    key_usage=st.text(min_size=1)
)
def test_key_attributes_required_properties(key_algorithm, key_class, key_usage):
    """Test that KeyAttributes validates required properties."""
    # Should work with all required properties
    key_modes = KeyModesOfUse(Encrypt=True)
    attrs = KeyAttributes(
        KeyAlgorithm=key_algorithm,
        KeyClass=key_class,
        KeyModesOfUse=key_modes,
        KeyUsage=key_usage
    )
    result = attrs.to_dict()
    assert result['KeyAlgorithm'] == key_algorithm
    assert result['KeyClass'] == key_class
    assert result['KeyUsage'] == key_usage
    
    # Should fail without required properties
    incomplete = KeyAttributes()
    with pytest.raises(ValueError, match='Resource .* required'):
        incomplete.to_dict()


@given(
    enabled_input=valid_boolean_inputs,
    exportable_input=valid_boolean_inputs
)
def test_key_boolean_properties(enabled_input, exportable_input):
    """Test that Key correctly processes boolean properties."""
    key_attrs = KeyAttributes(
        KeyAlgorithm='RSA_2048',
        KeyClass='PUBLIC_KEY',
        KeyModesOfUse=KeyModesOfUse(Encrypt=True),
        KeyUsage='ENCRYPT_DECRYPT'
    )
    
    key = Key(
        'TestKey',
        Enabled=enabled_input,
        Exportable=exportable_input,
        KeyAttributes=key_attrs
    )
    
    result = key.to_dict()
    # Boolean validator should normalize to True/False
    expected_enabled = validators.boolean(enabled_input)
    expected_exportable = validators.boolean(exportable_input)
    
    assert result['Properties']['Enabled'] == expected_enabled
    assert result['Properties']['Exportable'] == expected_exportable


@given(st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=100),
    min_size=1,
    max_size=10
))
def test_tags_round_trip(tags_dict):
    """Test that Tags can be created and serialized correctly."""
    # Create Key with Tags
    key_attrs = KeyAttributes(
        KeyAlgorithm='RSA_2048',
        KeyClass='PUBLIC_KEY',
        KeyModesOfUse=KeyModesOfUse(Encrypt=True),
        KeyUsage='ENCRYPT_DECRYPT'
    )
    
    tags = Tags(**tags_dict)
    key = Key(
        'TestKey',
        Exportable=True,
        KeyAttributes=key_attrs,
        Tags=tags
    )
    
    result = key.to_dict()
    # Tags should be serialized as a list of dicts with Key and Value
    assert 'Tags' in result['Properties']
    tags_list = result['Properties']['Tags']
    
    # Verify all tags are present
    tags_dict_from_list = {tag['Key']: tag['Value'] for tag in tags_list}
    assert tags_dict_from_list == tags_dict


@given(
    st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cs']), min_size=1),
    st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cs']), min_size=1)
)
def test_json_serialization_doesnt_crash(alias_name, key_arn):
    """Test that objects can be serialized to JSON without errors."""
    alias = Alias('TestAlias', AliasName=alias_name, KeyArn=key_arn)
    
    # Should be able to convert to JSON
    json_str = alias.to_json()
    assert isinstance(json_str, str)
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed['Properties']['AliasName'] == alias_name
    if key_arn:
        assert parsed['Properties']['KeyArn'] == key_arn


@given(st.data())
def test_nested_object_round_trip(data):
    """Test round-trip for nested objects (Key with KeyAttributes with KeyModesOfUse)."""
    # Generate random boolean values for KeyModesOfUse
    key_modes_kwargs = {}
    for prop in ['Decrypt', 'DeriveKey', 'Encrypt', 'Generate', 
                 'NoRestrictions', 'Sign', 'Unwrap', 'Verify', 'Wrap']:
        if data.draw(st.booleans()):
            key_modes_kwargs[prop] = data.draw(st.booleans())
    
    if not key_modes_kwargs:
        key_modes_kwargs['Encrypt'] = True
    
    key_modes = KeyModesOfUse(**key_modes_kwargs)
    
    key_attrs = KeyAttributes(
        KeyAlgorithm=data.draw(st.text(min_size=1)),
        KeyClass=data.draw(st.text(min_size=1)),
        KeyModesOfUse=key_modes,
        KeyUsage=data.draw(st.text(min_size=1))
    )
    
    key = Key(
        'TestKey',
        Exportable=data.draw(st.booleans()),
        KeyAttributes=key_attrs
    )
    
    # Serialize
    dict_repr = key.to_dict()
    json_repr = json.dumps(dict_repr)
    
    # Parse back
    parsed = json.loads(json_repr)
    
    # Verify structure is preserved
    assert parsed['Type'] == 'AWS::PaymentCryptography::Key'
    assert 'Properties' in parsed
    assert 'KeyAttributes' in parsed['Properties']
    assert 'KeyModesOfUse' in parsed['Properties']['KeyAttributes']
    
    # Verify values are preserved
    for prop, value in key_modes_kwargs.items():
        if prop in parsed['Properties']['KeyAttributes']['KeyModesOfUse']:
            assert parsed['Properties']['KeyAttributes']['KeyModesOfUse'][prop] == value