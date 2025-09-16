import json
from hypothesis import given, strategies as st, assume
import troposphere.qldb as qldb


@given(
    deletion_protection=st.booleans(),
    kms_key=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    name=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    permissions_mode=st.sampled_from(["ALLOW_ALL", "STANDARD"])
)
def test_ledger_to_dict_from_dict_roundtrip(deletion_protection, kms_key, name, permissions_mode):
    ledger = qldb.Ledger(
        'TestLedger',
        DeletionProtection=deletion_protection,
        KmsKey=kms_key,
        Name=name,
        PermissionsMode=permissions_mode
    )
    
    dict_repr = ledger.to_dict()
    
    new_ledger = qldb.Ledger.from_dict('ReconstructedLedger', dict_repr)
    new_dict_repr = new_ledger.to_dict()
    
    assert dict_repr == new_dict_repr


@given(
    aggregation_enabled=st.booleans(),
    stream_arn=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"]))
)
def test_kinesis_configuration_roundtrip(aggregation_enabled, stream_arn):
    config = qldb.KinesisConfiguration(
        AggregationEnabled=aggregation_enabled,
        StreamArn=stream_arn
    )
    
    dict_repr = config.to_dict()
    
    assert 'StreamArn' in dict_repr
    assert dict_repr['StreamArn'] == stream_arn
    if aggregation_enabled is not None:
        assert 'AggregationEnabled' in dict_repr


@given(
    ledger_name=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    role_arn=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    stream_name=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    inclusive_start_time=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    kinesis_stream_arn=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"]))
)
def test_stream_with_nested_configuration(ledger_name, role_arn, stream_name, inclusive_start_time, kinesis_stream_arn):
    config = qldb.KinesisConfiguration(StreamArn=kinesis_stream_arn)
    stream = qldb.Stream(
        'TestStream',
        LedgerName=ledger_name,
        RoleArn=role_arn,
        StreamName=stream_name,
        InclusiveStartTime=inclusive_start_time,
        KinesisConfiguration=config
    )
    
    dict_repr = stream.to_dict()
    
    assert 'Properties' in dict_repr
    props = dict_repr['Properties']
    assert props['LedgerName'] == ledger_name
    assert props['RoleArn'] == role_arn
    assert props['StreamName'] == stream_name
    assert props['InclusiveStartTime'] == inclusive_start_time
    assert 'KinesisConfiguration' in props
    assert props['KinesisConfiguration']['StreamArn'] == kinesis_stream_arn


@given(
    ledger_name=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    permissions_mode=st.sampled_from(["ALLOW_ALL", "STANDARD"])
)
def test_ledger_json_serialization(ledger_name, permissions_mode):
    ledger = qldb.Ledger(
        'TestLedger',
        Name=ledger_name,
        PermissionsMode=permissions_mode
    )
    
    json_str = ledger.to_json()
    
    parsed = json.loads(json_str)
    
    assert parsed['Type'] == 'AWS::QLDB::Ledger'
    assert parsed['Properties']['Name'] == ledger_name
    assert parsed['Properties']['PermissionsMode'] == permissions_mode


@given(st.booleans())
def test_boolean_function(value):
    from troposphere import boolean
    result = boolean(value)
    
    if value:
        assert result == "true"
    else:
        assert result == "false"


@given(
    ledger_name=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    role_arn=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    stream_name=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    inclusive_start_time=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    exclusive_end_time=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    kinesis_stream_arn=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"]))
)
def test_stream_roundtrip_with_all_fields(ledger_name, role_arn, stream_name, inclusive_start_time, exclusive_end_time, kinesis_stream_arn):
    config = qldb.KinesisConfiguration(StreamArn=kinesis_stream_arn)
    stream = qldb.Stream(
        'TestStream',
        LedgerName=ledger_name,
        RoleArn=role_arn,
        StreamName=stream_name,
        InclusiveStartTime=inclusive_start_time,
        ExclusiveEndTime=exclusive_end_time,
        KinesisConfiguration=config
    )
    
    dict_repr = stream.to_dict()
    new_stream = qldb.Stream.from_dict('ReconstructedStream', dict_repr)
    new_dict_repr = new_stream.to_dict()
    
    assert dict_repr == new_dict_repr