#!/usr/bin/env python3
"""Test for validation timing bug in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.mediastore import MetricPolicyRule, MetricPolicy

print("Testing validation timing...")
print("=" * 60)

# Test 1: Can we create an invalid MetricPolicyRule?
print("\n1. Creating MetricPolicyRule without required fields...")
try:
    # This should fail according to the schema (both fields are required)
    rule = MetricPolicyRule()
    print("   ✓ MetricPolicyRule() created successfully (no validation at init)")
    
    # Now try to convert to dict
    try:
        result = rule.to_dict()
        print(f"   ✗ BUG: to_dict() succeeded with missing required fields!")
        print(f"   Result: {result}")
    except ValueError as e:
        print(f"   ✓ to_dict() raised ValueError: {e}")
        
except TypeError as e:
    print(f"   ✓ MetricPolicyRule() raised TypeError (validation at init): {e}")

# Test 2: Can we create with only one required field?
print("\n2. Creating MetricPolicyRule with only ObjectGroup...")
try:
    rule = MetricPolicyRule(ObjectGroup="test")
    print("   ✓ MetricPolicyRule(ObjectGroup='test') created")
    
    try:
        result = rule.to_dict()
        print(f"   ✗ BUG: to_dict() succeeded with missing ObjectGroupName!")
        print(f"   Result: {result}")
    except ValueError as e:
        print(f"   ✓ to_dict() raised ValueError: {e}")
        
except TypeError as e:
    print(f"   ✓ Raised TypeError at init: {e}")

# Test 3: Invalid value for ContainerLevelMetrics
print("\n3. Creating MetricPolicy with invalid ContainerLevelMetrics...")
try:
    policy = MetricPolicy(ContainerLevelMetrics="INVALID")
    print("   ✓ MetricPolicy created with invalid status (no validation at init)")
    
    try:
        result = policy.to_dict()
        print(f"   ✗ BUG: to_dict() succeeded with invalid status!")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ✓ to_dict() raised {type(e).__name__}: {e}")
        
except ValueError as e:
    print(f"   ✓ Raised ValueError at init: {e}")

print("\n" + "=" * 60)
print("FINDING: Validation happens at to_dict() time, not at object creation.")
print("This allows creating invalid objects that fail later when serialized.")
print("\nIs this a bug? Let's check if this causes practical issues...")

# Test 4: Can this cause issues in normal usage?
print("\n4. Testing practical implications...")
try:
    # Create an invalid object
    bad_rule = MetricPolicyRule(ObjectGroup="test")  # Missing ObjectGroupName
    
    # This might be passed around in code
    rules_list = [bad_rule]
    
    # Later, when trying to generate CloudFormation...
    policy = MetricPolicy(
        ContainerLevelMetrics="ENABLED",
        MetricPolicyRules=rules_list
    )
    
    # The error only surfaces here, far from where the bug was introduced
    result = policy.to_dict()
    print(f"   ✗ BUG: Successfully serialized invalid structure!")
    
except ValueError as e:
    print(f"   ✓ Error caught (but late): {e}")
    print("\n   ISSUE: Error happens far from where invalid object was created.")
    print("   This makes debugging harder as the stack trace doesn't show")
    print("   where the invalid MetricPolicyRule was actually created.")