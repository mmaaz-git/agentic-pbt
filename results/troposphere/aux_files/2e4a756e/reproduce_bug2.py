#!/usr/bin/env python3
"""Bug 2: ExecutionPlan rejects None for optional fields"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kendraranking as kr

# Description is optional (False in props definition)
# But passing None causes TypeError
try:
    plan = kr.ExecutionPlan(
        "MyPlan",
        Name="TestPlan",
        Description=None  # Optional field should accept None
    )
    print("Success: Created plan with Description=None")
except TypeError as e:
    print(f"TypeError: {e}")
    print("BUG: Optional field Description doesn't accept None")

# Test with empty string
try:
    plan2 = kr.ExecutionPlan(
        "MyPlan2",
        Name="TestPlan2",
        Description=""  # Empty string works
    )
    print("Success: Created plan with Description=''")
except TypeError as e:
    print(f"TypeError: {e}")