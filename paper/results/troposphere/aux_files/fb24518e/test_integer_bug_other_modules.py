#!/usr/bin/env python3
"""
Test if integer validator bug affects other troposphere modules too.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Test with a different troposphere module
import troposphere.ec2 as ec2

# EC2 SecurityGroupRule has FromPort and ToPort which should be integers
rule = ec2.SecurityGroupRule(
    "TestRule",
    IpProtocol="tcp",
    FromPort=80.0,  # Float instead of int
    ToPort=443.0,   # Float instead of int  
    CidrIp="0.0.0.0/0"
)

rule_dict = rule.to_dict()
print(f"SecurityGroupRule.FromPort: {rule_dict.get('FromPort')} (type: {type(rule_dict.get('FromPort')).__name__})")
print(f"SecurityGroupRule.ToPort: {rule_dict.get('ToPort')} (type: {type(rule_dict.get('ToPort')).__name__})")

if isinstance(rule_dict.get('FromPort'), float):
    print("\nBug confirmed: Integer validator bug affects the entire troposphere library!")
    print("This is a systemic issue in troposphere.validators.integer()")
else:
    print("\nInteresting: EC2 module doesn't have the bug")