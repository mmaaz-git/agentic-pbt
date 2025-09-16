import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
from troposphere import athena
import json


@given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"]), min_size=1))
def test_workgroup_json_roundtrip(name):
    wg = athena.WorkGroup("TestWorkGroup", Name=name)
    json_str = wg.to_json()
    parsed = json.loads(json_str)
    assert parsed["Properties"]["Name"] == name


@given(st.integers(min_value=0))
def test_bytes_scanned_cutoff_accepts_large_values(value):
    wgc = athena.WorkGroupConfiguration(BytesScannedCutoffPerQuery=value)
    assert wgc.BytesScannedCutoffPerQuery == value


@given(st.text(min_size=1), st.text(min_size=1))
def test_prepared_statement_required_fields(statement_name, query_statement):
    ps = athena.PreparedStatement(
        "TestPreparedStatement",
        StatementName=statement_name,
        QueryStatement=query_statement,
        WorkGroup="default"
    )
    assert ps.StatementName == statement_name
    assert ps.QueryStatement == query_statement
    assert ps.WorkGroup == "default"


@given(st.sampled_from(["BUCKET_OWNER_FULL_CONTROL", "BUCKET_OWNER_READ"]))
def test_acl_configuration_s3_option(option):
    acl = athena.AclConfiguration(S3AclOption=option)
    assert acl.S3AclOption == option


@given(st.text())
def test_datacatalog_connection_type(conn_type):
    dc = athena.DataCatalog("TestCatalog", Name="test", Type="HIVE", ConnectionType=conn_type)
    assert dc.ConnectionType == conn_type


@given(st.floats(min_value=1, max_value=1000))
def test_targetdpus_accepts_floats_bug(dpus):
    cr = athena.CapacityReservation("TestReservation", Name="test", TargetDpus=dpus)
    assert cr.TargetDpus == dpus
    dict_repr = cr.to_dict()
    assert dict_repr["Properties"]["TargetDpus"] == dpus


@given(st.text(), st.sampled_from([None, "", " "]))
def test_optional_fields_with_edge_values(name, description):
    if description is not None:
        wg = athena.WorkGroup("TestWorkGroup", Name=name, Description=description)
        assert wg.Description == description
    else:
        wg = athena.WorkGroup("TestWorkGroup", Name=name)


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_datacatalog_parameters(params):
    dc = athena.DataCatalog("TestCatalog", Name="test", Type="HIVE", Parameters=params)
    assert dc.Parameters == params
    dict_repr = dc.to_dict()
    assert dict_repr["Properties"]["Parameters"] == params


@given(st.sampled_from([0, -1, -100]))
def test_negative_targetdpus(dpus):
    cr = athena.CapacityReservation("TestReservation", Name="test", TargetDpus=dpus)
    assert cr.TargetDpus == dpus