"""
Investigate the potential bugs found in troposphere.route53
"""

import troposphere.route53 as r53
import inspect

print("=== Bug 1: HostedZone Name field not in to_dict() ===")
# Check HostedZone props definition
print(f"HostedZone props: {r53.HostedZone.props}")

# Create a HostedZone with Name
hz = r53.HostedZone(
    title='TestZone', 
    Name='example.com'
)

# Check what's in the dict
dict_repr = hz.to_dict()
print(f"HostedZone dict: {dict_repr}")
print(f"'Name' in dict: {'Name' in dict_repr}")

# Check if Name is a property of the object
print(f"hz.Name attribute: {getattr(hz, 'Name', 'NOT FOUND')}")

# Check parent class
print(f"HostedZone bases: {r53.HostedZone.__bases__}")

print("\n=== Bug 2: HealthCheckConfig ResourcePath cannot be None ===")
# Check HealthCheckConfig props
print(f"HealthCheckConfig props: {r53.HealthCheckConfig.props}")

# Try with empty string
try:
    config1 = r53.HealthCheckConfig(
        IPAddress='1.2.3.4',
        Port=80,
        Type='HTTP',
        ResourcePath=''  # Empty string
    )
    print(f"Empty string ResourcePath: SUCCESS - {config1.to_dict()}")
except Exception as e:
    print(f"Empty string ResourcePath: ERROR - {e}")

# Try with None
try:
    config2 = r53.HealthCheckConfig(
        IPAddress='1.2.3.4',
        Port=80,
        Type='HTTP',
        ResourcePath=None  # None
    )
    print(f"None ResourcePath: SUCCESS - {config2.to_dict()}")
except Exception as e:
    print(f"None ResourcePath: ERROR - {e}")

# Try without ResourcePath
try:
    config3 = r53.HealthCheckConfig(
        IPAddress='1.2.3.4',
        Port=80,
        Type='HTTP'
        # No ResourcePath
    )
    print(f"No ResourcePath: SUCCESS - {config3.to_dict()}")
except Exception as e:
    print(f"No ResourcePath: ERROR - {e}")

# Check if ResourcePath is required
prop_definition = r53.HealthCheckConfig.props.get('ResourcePath')
print(f"\nResourcePath prop definition: {prop_definition}")
if prop_definition:
    print(f"ResourcePath required: {prop_definition[1] if len(prop_definition) > 1 else 'Unknown'}")