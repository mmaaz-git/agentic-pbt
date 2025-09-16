from troposphere.ssmquicksetup import ConfigurationDefinition, ConfigurationManager

# Create a valid ConfigurationManager
cd = ConfigurationDefinition(
    Parameters={'key': 'value'},
    Type='TestType'
)

cm1 = ConfigurationManager(
    'MyManager',
    ConfigurationDefinitions=[cd],
    Name='TestName'
)

# Convert to dict (CloudFormation format)
dict1 = cm1.to_dict()
print("to_dict() output:")
print(dict1)
print()

# Try to recreate from dict - this will fail
try:
    cm2 = ConfigurationManager.from_dict('MyManager', dict1)
    print("from_dict() succeeded")
    dict2 = cm2.to_dict()
    print("Round-trip successful:", dict1 == dict2)
except AttributeError as e:
    print(f"from_dict() failed with AttributeError: {e}")
    print()
    print("This violates the round-trip property:")
    print("  from_dict(to_dict(x)) should equal x")
    print()
    print("The issue is that to_dict() outputs CloudFormation format with 'Properties' key,")
    print("but from_dict() expects properties at the top level.")