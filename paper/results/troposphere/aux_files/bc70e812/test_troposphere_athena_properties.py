import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.athena as athena
from troposphere.validators import boolean, integer
from troposphere.validators.athena import validate_workgroup_state, validate_encryptionoption


@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_true_values(value):
    result = boolean(value)
    assert result is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))  
def test_boolean_false_values(value):
    result = boolean(value)
    assert result is False


@given(st.sampled_from([True, False, 0, 1, "0", "1", "true", "false", "True", "False"]))
def test_boolean_idempotence(value):
    result1 = boolean(value)
    result2 = boolean(result1)
    assert result1 == result2


@given(st.one_of(
    st.text().filter(lambda x: x not in ["0", "1", "true", "false", "True", "False"]),
    st.integers(min_value=2),
    st.integers(max_value=-1),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_invalid_raises_error(value):
    try:
        boolean(value)
        assert False, f"Expected ValueError for {value}"
    except ValueError:
        pass


@given(st.integers())
def test_integer_accepts_integers(value):
    result = integer(value)
    assert int(result) == value


@given(st.text(alphabet="0123456789", min_size=1))
def test_integer_accepts_numeric_strings(value):
    result = integer(value)
    assert int(result) == int(value)


@given(st.text(alphabet="0123456789-", min_size=1).filter(lambda x: x != "-"))
def test_integer_accepts_negative_strings(value):
    if value.startswith("-") and len(value) > 1 and value[1:].isdigit():
        result = integer(value)
        assert int(result) == int(value)


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: not x.is_integer()),
    st.text(min_size=1).filter(lambda x: not (x.lstrip("-").isdigit() if x else False)),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_invalid_raises_error(value):
    try:
        integer(value)
        assert False, f"Expected ValueError for {value}"
    except (ValueError, TypeError):
        pass


@given(st.sampled_from(["ENABLED", "DISABLED"]))
def test_validate_workgroup_state_valid(state):
    result = validate_workgroup_state(state)
    assert result == state


@given(st.text().filter(lambda x: x not in ["ENABLED", "DISABLED"]))
def test_validate_workgroup_state_invalid(state):
    try:
        validate_workgroup_state(state)
        assert False, f"Expected ValueError for {state}"
    except ValueError as e:
        assert "Workgroup State must be one of" in str(e)


@given(st.sampled_from(["ENABLED", "DISABLED"]))
def test_validate_workgroup_state_idempotent(state):
    result1 = validate_workgroup_state(state)
    result2 = validate_workgroup_state(result1)
    assert result1 == result2


@given(st.sampled_from(["CSE_KMS", "SSE_KMS", "SSE_S3"]))
def test_validate_encryptionoption_valid(option):
    result = validate_encryptionoption(option)
    assert result == option


@given(st.text().filter(lambda x: x not in ["CSE_KMS", "SSE_KMS", "SSE_S3"]))
def test_validate_encryptionoption_invalid(option):
    try:
        validate_encryptionoption(option)
        assert False, f"Expected ValueError for {option}"
    except ValueError as e:
        assert "EncryptionConfiguration EncryptionOption must be one of" in str(e)


@given(st.sampled_from(["CSE_KMS", "SSE_KMS", "SSE_S3"]))
def test_validate_encryptionoption_idempotent(option):
    result1 = validate_encryptionoption(option)
    result2 = validate_encryptionoption(result1)
    assert result1 == result2


@given(st.sampled_from(["enabled", "Enabled", "ENABLED ", " DISABLED", "disabled", "Disabled"]))
def test_validate_workgroup_state_case_sensitivity(state):
    if state in ["ENABLED", "DISABLED"]:
        result = validate_workgroup_state(state)
        assert result == state
    else:
        try:
            validate_workgroup_state(state)
            assert False, f"Expected ValueError for {state}"
        except ValueError:
            pass


@given(st.sampled_from(["cse_kms", "sse_kms", "sse_s3", "CSE_KMS ", " SSE_KMS"]))
def test_validate_encryptionoption_case_sensitivity(option):
    if option in ["CSE_KMS", "SSE_KMS", "SSE_S3"]:
        result = validate_encryptionoption(option)
        assert result == option
    else:
        try:
            validate_encryptionoption(option)
            assert False, f"Expected ValueError for {option}"
        except ValueError:
            pass


@given(st.integers(min_value=-2**63, max_value=2**63-1))
def test_integer_range_preservation(value):
    result = integer(value)
    assert int(result) == value


@given(st.sampled_from([2**31-1, 2**31, 2**32-1, 2**32, 2**63-1, -2**31, -2**32, -2**63]))
def test_integer_boundary_values(value):
    result = integer(value)
    assert int(result) == value


@given(st.sampled_from([True, False]))
def test_boolean_preserves_type(value):
    result = boolean(value)
    assert type(result) is bool
    assert result == value