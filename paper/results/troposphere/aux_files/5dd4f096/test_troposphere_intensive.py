import sys
import re
from hypothesis import given, strategies as st, assume, settings

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import organizations, BaseAWSObject
from troposphere.validators.organizations import validate_policy_type

# Test edge cases for validate_policy_type with more intensive testing
@given(st.text())
@settings(max_examples=1000)
def test_validate_policy_type_edge_cases(policy_type):
    valid_types = [
        "AISERVICES_OPT_OUT_POLICY",
        "BACKUP_POLICY", 
        "CHATBOT_POLICY",
        "DECLARATIVE_POLICY_EC2",
        "RESOURCE_CONTROL_POLICY",
        "SERVICE_CONTROL_POLICY",
        "TAG_POLICY",
    ]
    
    if policy_type in valid_types:
        result = validate_policy_type(policy_type)
        assert result == policy_type
    else:
        try:
            validate_policy_type(policy_type)
            assert False, f"Should have raised ValueError for invalid type: {policy_type}"
        except ValueError as e:
            assert "Type must be one of:" in str(e)

# Test with empty strings and special characters
@given(st.one_of(
    st.just(""),
    st.just(" "),
    st.just("\n"),
    st.just("\t"),
    st.text(alphabet="!@#$%^&*()[]{}|\\"),
    st.text().filter(lambda x: x and not x.strip())
))
@settings(max_examples=500)
def test_policy_type_special_chars(policy_type):
    try:
        validate_policy_type(policy_type)
        # Should only succeed for valid types (which none of these are)
        assert False, f"Should have raised ValueError for: {repr(policy_type)}"
    except ValueError as e:
        assert "Type must be one of:" in str(e)

# Test almost-valid policy types
@given(st.sampled_from([
    "BACKUP_POLICY ",  # trailing space
    " BACKUP_POLICY",  # leading space
    "backup_policy",   # lowercase
    "BACKUP_POLICY_",  # extra underscore
    "AISERVICES_OPT_OUT",  # missing _POLICY
    "SERVICE_CONTROL",  # missing _POLICY
    "TAG",  # missing _POLICY
]))
def test_almost_valid_policy_types(policy_type):
    try:
        validate_policy_type(policy_type)
        assert False, f"Should have raised ValueError for: {repr(policy_type)}"
    except ValueError as e:
        assert "Type must be one of:" in str(e)

# Test boundary conditions for title validation
@given(st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127)))
@settings(max_examples=1000)
def test_title_validation_ascii_range(title):
    valid_pattern = re.compile(r'^[a-zA-Z0-9]+$')
    
    try:
        org = organizations.Organization(title=title)
        # If we get here, title was accepted
        if title:
            assert valid_pattern.match(title), f"Title {repr(title)} should match pattern"
    except ValueError as e:
        if title:
            assert not valid_pattern.match(title), f"Title {repr(title)} should have been accepted"
            assert 'not alphanumeric' in str(e)

# Test with Unicode characters
@given(st.text(min_size=1, alphabet=st.characters(min_codepoint=128)))
@settings(max_examples=100)
def test_title_validation_unicode(title):
    # Unicode characters should be rejected
    try:
        org = organizations.Organization(title=title)
        assert False, f"Should have rejected Unicode title: {repr(title)}"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)

# Test empty and None titles
def test_title_edge_cases():
    # Empty string
    try:
        org = organizations.Organization(title="")
        # Empty titles might be accepted or rejected
    except ValueError as e:
        assert 'not alphanumeric' in str(e)
    
    # None title
    org = organizations.Organization(title=None)  # Should work
    assert org.title is None

# Test property types with extreme values
@given(
    name=st.text(min_size=0, max_size=10000),
    email=st.text(min_size=0, max_size=10000),
    parent_ids=st.lists(st.text(min_size=0, max_size=1000), min_size=0, max_size=100)
)
@settings(max_examples=100)
def test_account_extreme_sizes(name, email, parent_ids):
    try:
        account = organizations.Account(
            title="TestAccount",
            AccountName=name,
            Email=email,
            ParentIds=parent_ids
        )
        dict_repr = account.to_dict()
        props = dict_repr.get('Properties', {})
        assert props['AccountName'] == name
        assert props['Email'] == email
        if parent_ids:
            assert props['ParentIds'] == parent_ids
    except Exception:
        # Some extreme values might fail validation
        pass