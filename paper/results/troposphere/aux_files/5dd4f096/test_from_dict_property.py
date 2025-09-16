import sys
import re
from hypothesis import given, strategies as st, assume, settings

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import organizations

# Test the _from_dict method more thoroughly
@given(
    name=st.text(min_size=1).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x)),
    description=st.text(),
    content=st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers(), st.booleans())),
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
@settings(max_examples=500)
def test_policy_from_dict_round_trip(name, description, content, policy_type):
    # Create a Policy object
    policy1 = organizations.Policy(
        title="TestPolicy1",
        Name=name,
        Content=content,
        Type=policy_type,
        Description=description
    )
    
    # Convert to dict
    dict1 = policy1.to_dict()
    
    # Try to recreate using _from_dict
    props = dict1.get('Properties', {})
    
    # Create policy using _from_dict
    policy2 = organizations.Policy._from_dict(
        title="TestPolicy2",
        **props
    )
    
    # Convert the second policy to dict
    dict2 = policy2.to_dict()
    
    # Properties should match
    assert dict1.get('Properties') == dict2.get('Properties')
    assert dict1.get('Type') == dict2.get('Type')

# Test Account _from_dict with edge cases
@given(
    account_name=st.text(min_size=1),
    email=st.text(min_size=1),
    parent_ids=st.one_of(
        st.none(),
        st.lists(st.text(min_size=1), min_size=0, max_size=10)
    ),
    role_name=st.one_of(st.none(), st.text())
)
@settings(max_examples=500)
def test_account_from_dict_round_trip(account_name, email, parent_ids, role_name):
    kwargs = {
        'AccountName': account_name,
        'Email': email
    }
    if parent_ids is not None:
        kwargs['ParentIds'] = parent_ids
    if role_name is not None:
        kwargs['RoleName'] = role_name
    
    # Create Account
    account1 = organizations.Account(
        title="TestAccount1",
        **kwargs
    )
    
    # Convert to dict
    dict1 = account1.to_dict()
    props = dict1.get('Properties', {})
    
    # Create using _from_dict
    account2 = organizations.Account._from_dict(
        title="TestAccount2",
        **props
    )
    
    # Convert back to dict
    dict2 = account2.to_dict()
    
    # Should match
    assert dict1.get('Properties') == dict2.get('Properties')

# Test OrganizationalUnit _from_dict
@given(
    name=st.text(min_size=1),
    parent_id=st.text(min_size=1)
)
@settings(max_examples=500)
def test_org_unit_from_dict(name, parent_id):
    org_unit1 = organizations.OrganizationalUnit(
        title="TestOrgUnit1",
        Name=name,
        ParentId=parent_id
    )
    
    dict1 = org_unit1.to_dict()
    props = dict1.get('Properties', {})
    
    org_unit2 = organizations.OrganizationalUnit._from_dict(
        title="TestOrgUnit2",
        **props
    )
    
    dict2 = org_unit2.to_dict()
    
    assert dict1.get('Properties') == dict2.get('Properties')

# Test ResourcePolicy _from_dict
@given(
    content=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(
            st.text(),
            st.integers(),
            st.booleans(),
            st.lists(st.text(), max_size=5),
            st.dictionaries(st.text(min_size=1, max_size=10), st.text(), max_size=5)
        ),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=500)
def test_resource_policy_from_dict(content):
    policy1 = organizations.ResourcePolicy(
        title="TestResourcePolicy1",
        Content=content
    )
    
    dict1 = policy1.to_dict()
    props = dict1.get('Properties', {})
    
    policy2 = organizations.ResourcePolicy._from_dict(
        title="TestResourcePolicy2",
        **props
    )
    
    dict2 = policy2.to_dict()
    
    assert dict1.get('Properties') == dict2.get('Properties')