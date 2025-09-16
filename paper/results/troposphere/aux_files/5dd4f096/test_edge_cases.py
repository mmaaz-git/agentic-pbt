import sys
import re
from hypothesis import given, strategies as st, assume, settings, example

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import organizations

# Test what happens with title edge cases
@given(title=st.one_of(
    st.just(""),
    st.just(None),
    st.text(min_size=1).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x))
))
def test_organization_title_edge_cases(title):
    # Organization only has optional FeatureSet property
    try:
        org = organizations.Organization(title=title)
        dict_repr = org.to_dict()
        
        # Empty title should fail validation
        if title == "":
            assert False, "Empty title should have been rejected"
        
        # None title should work - it's allowed
        if title is None:
            assert org.title is None
        else:
            # Valid alphanumeric title
            assert org.title == title
            
    except ValueError as e:
        # Should only fail for empty string
        if title == "":
            assert 'not alphanumeric' in str(e)
        else:
            raise  # Unexpected error

# Test what happens when mixing valid and invalid data in lists
@given(
    valid_ids=st.lists(st.text(min_size=1, alphabet=st.characters(categories=['L', 'N'])), min_size=1, max_size=5),
    insert_empty=st.booleans()
)
def test_account_parent_ids_with_empty(valid_ids, insert_empty):
    parent_ids = list(valid_ids)
    if insert_empty:
        parent_ids.insert(len(parent_ids) // 2, "")  # Insert empty string in middle
    
    account = organizations.Account(
        title="TestAccount",
        AccountName="TestName",
        Email="test@example.com",
        ParentIds=parent_ids
    )
    
    dict_repr = account.to_dict()
    props = dict_repr.get('Properties', {})
    
    # ParentIds should preserve all values including empty strings
    if parent_ids:
        assert props['ParentIds'] == parent_ids

# Test interaction between multiple properties
@given(
    name=st.text(min_size=1),
    parent_id=st.text(min_size=1),
    tags_dict=st.one_of(
        st.none(),
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(max_size=200),
            min_size=0,
            max_size=10
        )
    )
)
@settings(max_examples=200)
def test_organizational_unit_with_tags(name, parent_id, tags_dict):
    kwargs = {
        'Name': name,
        'ParentId': parent_id
    }
    
    if tags_dict is not None:
        # Tags in troposphere are typically a list of dicts with Key and Value
        tags = [{'Key': k, 'Value': v} for k, v in tags_dict.items()]
        kwargs['Tags'] = tags
    
    org_unit = organizations.OrganizationalUnit(
        title="TestOrgUnit",
        **kwargs
    )
    
    dict_repr = org_unit.to_dict()
    props = dict_repr.get('Properties', {})
    
    assert props['Name'] == name
    assert props['ParentId'] == parent_id
    if tags_dict is not None and tags_dict:
        assert 'Tags' in props

# Test Policy with nested dict content
@given(
    content=st.recursive(
        st.one_of(
            st.text(),
            st.integers(),
            st.booleans(),
            st.none()
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=3),
            st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=3)
        ),
        max_leaves=20
    ),
    policy_type=st.sampled_from([
        "SERVICE_CONTROL_POLICY",
        "TAG_POLICY",
    ])
)
@settings(max_examples=100)
def test_policy_with_complex_content(content, policy_type):
    # If content is not a dict, wrap it
    if not isinstance(content, dict):
        content = {'value': content}
    
    policy = organizations.Policy(
        title="TestPolicy",
        Name="TestPolicyName",
        Content=content,
        Type=policy_type
    )
    
    dict_repr = policy.to_dict()
    props = dict_repr.get('Properties', {})
    
    assert props['Content'] == content
    assert props['Type'] == policy_type

# Test that numeric titles are accepted
@given(number=st.integers(min_value=0, max_value=999999999))
def test_numeric_titles(number):
    title = str(number)
    
    # Numeric strings should be valid (they match [a-zA-Z0-9]+)
    org = organizations.Organization(title=title)
    assert org.title == title
    
    dict_repr = org.to_dict()
    assert dict_repr['Type'] == 'AWS::Organizations::Organization'

# Test mixed alphanumeric titles
@given(st.from_regex(r'^[a-zA-Z0-9]{1,50}$'))
def test_valid_alphanumeric_titles(title):
    account = organizations.Account(
        title=title,
        AccountName="TestAccount",
        Email="test@example.com"
    )
    
    assert account.title == title
    dict_repr = account.to_dict()
    assert dict_repr['Type'] == 'AWS::Organizations::Account'