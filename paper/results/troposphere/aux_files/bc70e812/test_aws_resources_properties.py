import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
from troposphere import athena
import json


@given(st.text(min_size=1))
def test_workgroup_name_preserved(name):
    wg = athena.WorkGroup("TestWorkGroup", Name=name)
    assert wg.Name == name
    dict_repr = wg.to_dict()
    assert dict_repr["Properties"]["Name"] == name


@given(st.sampled_from(["ENABLED", "DISABLED"]))
def test_workgroup_state_roundtrip(state):
    wg = athena.WorkGroup("TestWorkGroup", Name="test", State=state)
    assert wg.State == state
    dict_repr = wg.to_dict()
    assert dict_repr["Properties"]["State"] == state


@given(st.text(min_size=1), st.text(min_size=1))
def test_namedquery_properties_preserved(database, query_string):
    nq = athena.NamedQuery("TestQuery", Database=database, QueryString=query_string)
    assert nq.Database == database
    assert nq.QueryString == query_string
    dict_repr = nq.to_dict()
    assert dict_repr["Properties"]["Database"] == database
    assert dict_repr["Properties"]["QueryString"] == query_string


@given(st.integers(min_value=1, max_value=1000))
def test_capacity_reservation_targetdpus(dpus):
    cr = athena.CapacityReservation("TestReservation", Name="test", TargetDpus=dpus)
    assert cr.TargetDpus == dpus
    dict_repr = cr.to_dict()
    assert dict_repr["Properties"]["TargetDpus"] == dpus


@given(st.sampled_from(["CSE_KMS", "SSE_KMS", "SSE_S3"]), st.text(min_size=1))
def test_encryption_configuration_properties(option, kms_key):
    ec = athena.EncryptionConfiguration(EncryptionOption=option, KmsKey=kms_key)
    assert ec.EncryptionOption == option
    assert ec.KmsKey == kms_key


@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_capacity_assignment_workgroup_names(names):
    ca = athena.CapacityAssignment(WorkgroupNames=names)
    assert ca.WorkgroupNames == names


@given(st.text(min_size=1).filter(lambda x: x not in ["ENABLED", "DISABLED"]))
def test_workgroup_invalid_state_raises(state):
    try:
        athena.WorkGroup("TestWorkGroup", Name="test", State=state)
        assert False, f"Expected ValueError for state: {state}"
    except ValueError as e:
        assert "Workgroup State must be one of" in str(e)


@given(st.text(min_size=1).filter(lambda x: x not in ["CSE_KMS", "SSE_KMS", "SSE_S3"]))
def test_encryption_invalid_option_raises(option):
    try:
        athena.EncryptionConfiguration(EncryptionOption=option)
        assert False, f"Expected ValueError for option: {option}"
    except ValueError as e:
        assert "EncryptionConfiguration EncryptionOption must be one of" in str(e)


@given(st.booleans())
def test_workgroup_recursive_delete_option(value):
    wg = athena.WorkGroup("TestWorkGroup", Name="test", RecursiveDeleteOption=value)
    assert wg.RecursiveDeleteOption == value
    dict_repr = wg.to_dict()
    assert dict_repr["Properties"]["RecursiveDeleteOption"] == value


@given(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]))
def test_managed_query_results_enabled_boolean_coercion(value):
    from troposphere.validators import boolean
    expected = boolean(value)
    mqr = athena.ManagedQueryResultsConfiguration(Enabled=value)
    assert mqr.Enabled == expected