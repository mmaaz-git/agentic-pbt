#!/usr/bin/env python3
"""Check if omitting optional field works vs passing None"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kendraranking as kr

# Test 1: Omit Description entirely
try:
    plan1 = kr.ExecutionPlan(
        "Plan1",
        Name="TestPlan1"
        # Description omitted
    )
    print("Success: Created plan without Description field")
    print(f"Properties: {plan1.properties}")
except Exception as e:
    print(f"Failed without Description: {e}")

# Test 2: Pass None explicitly  
try:
    plan2 = kr.ExecutionPlan(
        "Plan2",
        Name="TestPlan2",
        Description=None
    )
    print("Success: Created plan with Description=None")
except Exception as e:
    print(f"Failed with Description=None: {e}")

# Test 3: Check the props definition
print(f"\nExecutionPlan props: {kr.ExecutionPlan.props}")
print(f"Description required? {kr.ExecutionPlan.props['Description'][1]}")