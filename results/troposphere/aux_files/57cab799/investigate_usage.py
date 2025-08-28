#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.auditmanager import *
from troposphere.validators import double
import inspect

print("=== Testing double function ===")
# Test what the double function accepts/rejects
test_cases = [
    1, 1.5, "2.5", "3", 0, -1, -1.5, float('inf'), 
    True, False, None, "not_a_number", [], {}
]

for val in test_cases:
    try:
        result = double(val)
        print(f"double({repr(val)}) = {repr(result)}")
    except Exception as e:
        print(f"double({repr(val)}) raised: {e}")

print("\n=== Testing Delegation with CreationTime ===")
# Test that CreationTime property uses double
try:
    d1 = Delegation(CreationTime=123.456)
    print(f"Delegation with float CreationTime: {d1.to_dict()}")
    
    d2 = Delegation(CreationTime="789.012")
    print(f"Delegation with string CreationTime: {d2.to_dict()}")
    
    d3 = Delegation(CreationTime=100)
    print(f"Delegation with int CreationTime: {d3.to_dict()}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Testing Assessment to_dict/from_dict ===")
# Test round-trip
assessment = Assessment(
    "TestAssessment",
    Name="MyAssessment",
    Description="Test Description",
    Status="ACTIVE"
)
dict_repr = assessment.to_dict()
print(f"Original dict: {dict_repr}")

# Try from_dict
try:
    reconstructed = Assessment.from_dict("TestAssessment2", dict_repr["Properties"])
    print(f"Reconstructed dict: {reconstructed.to_dict()}")
    print(f"Equal? {assessment.to_dict() == reconstructed.to_dict()}")
except Exception as e:
    print(f"from_dict error: {e}")

print("\n=== Testing validation requirements ===")
# Check if any properties are required
for cls_name in ['Assessment', 'Delegation', 'AWSAccount', 'Role']:
    cls = globals()[cls_name]
    required = [(k, v[1]) for k, v in cls.props.items() if v[1]]
    print(f"{cls_name} required props: {required if required else 'None'}")