"""
Test to demonstrate that troposphere.Parameter accepts invalid Type values
that would result in invalid CloudFormation templates.
"""

from hypothesis import given, strategies as st
import troposphere
from troposphere import Template, Parameter
import json


# Valid CloudFormation parameter types according to AWS documentation
VALID_PARAMETER_TYPES = {
    'String',
    'Number',
    'List<Number>',
    'CommaDelimitedList',
    # AWS-specific parameter types
    'AWS::EC2::AvailabilityZone::Name',
    'AWS::EC2::Image::Id',
    'AWS::EC2::Instance::Id',
    'AWS::EC2::KeyPair::KeyName',
    'AWS::EC2::SecurityGroup::GroupName',
    'AWS::EC2::SecurityGroup::Id',
    'AWS::EC2::Subnet::Id',
    'AWS::EC2::Volume::Id',
    'AWS::EC2::VPC::Id',
    'AWS::Route53::HostedZone::Id',
    'List<AWS::EC2::AvailabilityZone::Name>',
    'List<AWS::EC2::Image::Id>',
    'List<AWS::EC2::Instance::Id>',
    'List<AWS::EC2::SecurityGroup::GroupName>',
    'List<AWS::EC2::SecurityGroup::Id>',
    'List<AWS::EC2::Subnet::Id>',
    'List<AWS::EC2::Volume::Id>',
    'List<AWS::EC2::VPC::Id>',
    'List<AWS::Route53::HostedZone::Id>',
    # SSM parameter types
    'AWS::SSM::Parameter::Name',
    'AWS::SSM::Parameter::Value<String>',
    'AWS::SSM::Parameter::Value<List<String>>',
    'AWS::SSM::Parameter::Value<CommaDelimitedList>',
}


@given(st.text().filter(lambda s: s not in VALID_PARAMETER_TYPES))
def test_parameter_accepts_invalid_types(invalid_type):
    """Test that Parameter accepts invalid Type values without validation"""
    
    # This should ideally raise a validation error, but it doesn't
    p = Parameter('TestParam', Type=invalid_type)
    
    # The parameter is created successfully
    assert p.title == 'TestParam'
    assert p.properties['Type'] == invalid_type
    
    # It can be added to a template
    t = Template()
    t.add_parameter(p)
    
    # And converted to JSON
    json_str = t.to_json()
    parsed = json.loads(json_str)
    
    # The invalid type is preserved in the output
    assert parsed['Parameters']['TestParam']['Type'] == invalid_type
    
    # This would be an invalid CloudFormation template!
    # CloudFormation would reject this when you try to create/update a stack


def test_empty_string_type_bug():
    """Demonstrate that empty string Type creates invalid CloudFormation"""
    # Empty string is definitely not a valid CloudFormation parameter type
    p = Parameter('EmptyTypeParam', Type='')
    t = Template()
    t.add_parameter(p)
    
    # This creates invalid CloudFormation JSON
    json_str = t.to_json()
    parsed = json.loads(json_str)
    
    assert parsed['Parameters']['EmptyTypeParam']['Type'] == ''
    # CloudFormation would reject this!


def test_common_typo_types_accepted():
    """Test that common typos in parameter types are accepted"""
    
    # These are common typos/mistakes that should be caught
    invalid_but_accepted = [
        'string',  # lowercase (should be 'String')
        'number',  # lowercase (should be 'Number')  
        'Integer',  # wrong name (should be 'Number')
        'Boolean',  # doesn't exist in CloudFormation
        'Bool',  # doesn't exist
        'Array',  # should be List<Type> or CommaDelimitedList
        'Object',  # doesn't exist
        'JSON',  # doesn't exist
    ]
    
    for invalid_type in invalid_but_accepted:
        # None of these should work, but they all do
        p = Parameter(f'Param', Type=invalid_type)
        t = Template()
        t.add_parameter(p)
        json_str = t.to_json()
        
        # Verify the invalid type made it into the JSON
        parsed = json.loads(json_str)
        assert parsed['Parameters']['Param']['Type'] == invalid_type
        
        print(f"Accepted invalid type: {invalid_type}")


if __name__ == '__main__':
    test_empty_string_type_bug()
    test_common_typo_types_accepted()
    print("\nBug confirmed: Parameter accepts invalid Type values that would create invalid CloudFormation templates")