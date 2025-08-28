import hypothesis.strategies as st
from hypothesis import given, assume, settings
import troposphere.systemsmanagersap as sap


# Strategy for valid AWS resource IDs and names
aws_id_strategy = st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='\\'), min_size=1, max_size=255)
aws_type_strategy = st.sampled_from(['SAP/HANA', 'SAP/ABAP', 'SAP/S4HANA', 'SAP/ECC', 'SAP/BW'])
credential_type_strategy = st.sampled_from(['ADMIN', 'USER', 'SERVICE', 'SYSTEM'])
component_type_strategy = st.sampled_from(['ASCS', 'DB', 'ERS', 'HANA', 'JAVA', 'ABAP'])

# Property 1: Round-trip property for Application with required fields
@given(
    title=aws_id_strategy,
    app_id=aws_id_strategy,
    app_type=aws_type_strategy
)
def test_application_roundtrip_required_fields(title, app_id, app_type):
    """Test that Application.from_dict(app.to_dict()) preserves data with required fields only"""
    # Create an Application with required fields
    app1 = sap.Application(title, ApplicationId=app_id, ApplicationType=app_type)
    
    # Convert to dict
    dict1 = app1.to_dict()
    
    # The from_dict expects just the Properties, not the full dict
    # This is the bug - from_dict can't handle the output of to_dict
    props = dict1.get('Properties', {})
    
    # Create from dict
    app2 = sap.Application.from_dict(title + '_new', props)
    dict2 = app2.to_dict()
    
    # Check that the properties are preserved
    assert dict1['Properties'] == dict2['Properties']


# Property 2: Round-trip property for Application with all fields
@given(
    title=aws_id_strategy,
    app_id=aws_id_strategy,
    app_type=aws_type_strategy,
    db_arn=st.one_of(st.none(), aws_id_strategy),
    instance_num=st.one_of(st.none(), st.text(alphabet='0123456789', min_size=1, max_size=2)),
    sid=st.one_of(st.none(), st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=3)),
    instances=st.one_of(st.none(), st.lists(aws_id_strategy, min_size=0, max_size=5))
)
def test_application_roundtrip_all_fields(title, app_id, app_type, db_arn, instance_num, sid, instances):
    """Test that Application preserves all optional fields through round-trip"""
    kwargs = {
        'ApplicationId': app_id,
        'ApplicationType': app_type
    }
    
    if db_arn is not None:
        kwargs['DatabaseArn'] = db_arn
    if instance_num is not None:
        kwargs['SapInstanceNumber'] = instance_num
    if sid is not None:
        kwargs['Sid'] = sid
    if instances is not None:
        kwargs['Instances'] = instances
    
    app1 = sap.Application(title, **kwargs)
    dict1 = app1.to_dict()
    
    # Extract properties for from_dict
    props = dict1.get('Properties', {})
    app2 = sap.Application.from_dict(title + '_new', props)
    dict2 = app2.to_dict()
    
    assert dict1['Properties'] == dict2['Properties']


# Property 3: Round-trip for Credential
@given(
    cred_type=st.one_of(st.none(), credential_type_strategy),
    db_name=st.one_of(st.none(), aws_id_strategy),
    secret_id=st.one_of(st.none(), aws_id_strategy)
)
def test_credential_roundtrip(cred_type, db_name, secret_id):
    """Test that Credential.from_dict(cred.to_dict()) preserves data"""
    kwargs = {}
    if cred_type is not None:
        kwargs['CredentialType'] = cred_type
    if db_name is not None:
        kwargs['DatabaseName'] = db_name
    if secret_id is not None:
        kwargs['SecretId'] = secret_id
    
    # Skip if no properties (empty dict might not be valid)
    if not kwargs:
        assume(False)
    
    cred1 = sap.Credential(**kwargs)
    dict1 = cred1.to_dict()
    
    # Credential.from_dict expects a title and the dict
    cred2 = sap.Credential.from_dict('cred_title', dict1)
    dict2 = cred2.to_dict()
    
    assert dict1 == dict2


# Property 4: Round-trip for ComponentInfo
@given(
    comp_type=st.one_of(st.none(), component_type_strategy),
    instance_id=st.one_of(st.none(), aws_id_strategy),
    sid=st.one_of(st.none(), st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=3))
)
def test_componentinfo_roundtrip(comp_type, instance_id, sid):
    """Test that ComponentInfo.from_dict(comp.to_dict()) preserves data"""
    kwargs = {}
    if comp_type is not None:
        kwargs['ComponentType'] = comp_type
    if instance_id is not None:
        kwargs['Ec2InstanceId'] = instance_id
    if sid is not None:
        kwargs['Sid'] = sid
    
    # Skip if no properties
    if not kwargs:
        assume(False)
    
    comp1 = sap.ComponentInfo(**kwargs)
    dict1 = comp1.to_dict()
    
    comp2 = sap.ComponentInfo.from_dict('comp_title', dict1)
    dict2 = comp2.to_dict()
    
    assert dict1 == dict2


# Property 5: Test the actual bug - from_dict should handle to_dict output
@given(
    title=aws_id_strategy,
    app_id=aws_id_strategy,
    app_type=aws_type_strategy
)
def test_application_from_dict_handles_full_dict(title, app_id, app_type):
    """Test that Application.from_dict can handle the full output of to_dict (including Type and Properties wrapper)"""
    app1 = sap.Application(title, ApplicationId=app_id, ApplicationType=app_type)
    full_dict = app1.to_dict()
    
    # This should work but doesn't - it's the bug
    app2 = sap.Application.from_dict(title + '_new', full_dict)
    dict2 = app2.to_dict()
    
    # Properties should be preserved
    assert full_dict['Properties'] == dict2['Properties']