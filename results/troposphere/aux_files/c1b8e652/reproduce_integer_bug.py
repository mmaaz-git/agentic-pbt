"""
Minimal reproduction script for integer validator bugs in troposphere.vpclattice
"""
import troposphere.vpclattice as vpc
import json

print("=== Bug 1: Integer validator accepts strings without converting ===")

# Create HealthCheckConfig with string numbers
hc = vpc.HealthCheckConfig(
    'test',
    Port='8080',
    HealthCheckIntervalSeconds='30'
)

print(f"Input Port: '8080' (string)")
print(f"Stored Port type: {type(hc.properties['Port'])}")
print(f"Stored Port value: {hc.properties['Port']}")

# This is problematic when serializing to JSON and using with AWS
dict_output = hc.to_dict()
json_output = json.dumps(dict_output)
print(f"\nJSON output: {json_output}")
# AWS CloudFormation expects integer values, not strings

print("\n=== Bug 2: Integer validator accepts floats without converting ===")

hc2 = vpc.HealthCheckConfig(
    'test2',
    Port=8080.5,
    HealthCheckTimeoutSeconds=5.7
)

print(f"Input Port: 8080.5 (float)")
print(f"Stored Port type: {type(hc2.properties['Port'])}")
print(f"Stored Port value: {hc2.properties['Port']}")

# This is problematic because AWS expects integer values
dict_output2 = hc2.to_dict()
json_output2 = json.dumps(dict_output2)
print(f"\nJSON output: {json_output2}")

print("\n=== Expected behavior ===")
print("Integer validators should either:")
print("1. Convert valid inputs to integers (e.g., '8080' -> 8080, 8080.5 -> 8080)")
print("2. Reject invalid inputs with clear error messages")
print("\nInstead, they accept and store non-integer types, which can cause:")
print("- Type mismatches in CloudFormation templates")
print("- Validation errors when deploying to AWS")
print("- Unexpected behavior in downstream processing")