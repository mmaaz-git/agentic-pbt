#!/usr/bin/env python3
"""Minimal reproduction of RuleGroup requiring undocumented title argument"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.networkfirewall import RuleGroup

# Test 1: Creating RuleGroup without title fails
try:
    rule_group = RuleGroup(
        Capacity=100,
        RuleGroupName="test-group",
        Type="STATEFUL"
    )
    print("ERROR: Should have failed without title")
except TypeError as e:
    print(f"Failed as expected without title: {e}")

# Test 2: Creating RuleGroup with title works  
rule_group = RuleGroup(
    "MyRuleGroup",  # This is the title - required but not in props!
    Capacity=100,
    RuleGroupName="test-group",
    Type="STATEFUL"
)
print(f"\nSuccessfully created RuleGroup with title: {rule_group.title}")

# Test 3: Check if title is documented in props
print(f"\nRuleGroup.props keys: {list(RuleGroup.props.keys())}")
print(f"Is 'title' in props? {'title' in RuleGroup.props}")

# Test 4: Check the generated CloudFormation
result = rule_group.to_dict()
print(f"\nGenerated CloudFormation resource name: {rule_group.title}")
print(f"Resource type: {result.get('Type')}")
print(f"Properties: {result.get('Properties', {}).keys()}")