import sys
import re
from hypothesis import given, strategies as st, assume, settings

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import organizations, validators
from troposphere.validators.organizations import validate_policy_type

# Test 1: validate_policy_type accepts valid types and rejects invalid ones
@given(st.text())
def test_validate_policy_type_with_random_strings(policy_type):
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

# Test 2: Round-trip property for Policy objects
@given(
    name=st.text(min_size=1).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x)),
    description=st.text(),
    content=st.dictionaries(st.text(min_size=1), st.text()),
    policy_type=st.sampled_from([
        "AISERVICES_OPT_OUT_POLICY",
        "BACKUP_POLICY",
        "CHATBOT_POLICY",
        "DECLARATIVE_POLICY_EC2",
        "RESOURCE_CONTROL_POLICY",
        "SERVICE_CONTROL_POLICY",
        "TAG_POLICY",
    ])
)
@settings(max_examples=100)
def test_policy_round_trip(name, description, content, policy_type):
    # Create a Policy object
    policy = organizations.Policy(
        title="TestPolicy",
        Name=name,
        Content=content,
        Type=policy_type,
        Description=description
    )
    
    # Convert to dict
    policy_dict = policy.to_dict()
    
    # Extract properties for reconstruction
    props = policy_dict.get('Properties', {})
    
    # Create new policy from dict
    policy2 = organizations.Policy(
        title="TestPolicy2",
        Name=props.get('Name'),
        Content=props.get('Content'),
        Type=props.get('Type'),
        Description=props.get('Description')
    )
    
    # Check that properties match
    assert policy.Name == policy2.Name
    assert policy.Content == policy2.Content  
    assert policy.Type == policy2.Type
    assert policy.Description == policy2.Description

# Test 3: Title validation pattern
@given(st.text())
def test_title_validation_pattern(title):
    valid_pattern = re.compile(r'^[a-zA-Z0-9]+$')
    
    try:
        account = organizations.Account(
            title=title,
            AccountName="TestAccount",
            Email="test@example.com"
        )
        # If we get here, title was accepted
        if title:  # Non-empty titles should match pattern
            assert valid_pattern.match(title), f"Title '{title}' should match alphanumeric pattern"
    except ValueError as e:
        # Title was rejected
        if title:  # Non-empty titles that don't match should be rejected
            assert not valid_pattern.match(title), f"Title '{title}' should have been accepted"
            assert 'not alphanumeric' in str(e)

# Test 4: Required properties enforcement
@given(
    account_name=st.one_of(st.none(), st.text()),
    email=st.one_of(st.none(), st.text())
)
def test_required_properties(account_name, email):
    # Account requires AccountName and Email
    kwargs = {}
    if account_name is not None:
        kwargs['AccountName'] = account_name
    if email is not None:
        kwargs['Email'] = email
    
    try:
        account = organizations.Account(title="TestAccount", **kwargs)
        dict_repr = account.to_dict()
        # Check that properties were set
        props = dict_repr.get('Properties', {})
        if account_name is not None:
            assert 'AccountName' in props
        if email is not None:
            assert 'Email' in props
    except Exception:
        # Properties validation might fail for None values
        pass

# Test 5: OrganizationalUnit round-trip
@given(
    name=st.text(min_size=1),
    parent_id=st.text(min_size=1)
)
@settings(max_examples=100)
def test_org_unit_round_trip(name, parent_id):
    org_unit = organizations.OrganizationalUnit(
        title="TestOrgUnit",
        Name=name,
        ParentId=parent_id
    )
    
    dict_repr = org_unit.to_dict()
    props = dict_repr.get('Properties', {})
    
    org_unit2 = organizations.OrganizationalUnit(
        title="TestOrgUnit2",
        Name=props.get('Name'),
        ParentId=props.get('ParentId')
    )
    
    assert org_unit.Name == org_unit2.Name
    assert org_unit.ParentId == org_unit2.ParentId