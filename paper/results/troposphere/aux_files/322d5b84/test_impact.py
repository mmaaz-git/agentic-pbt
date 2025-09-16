#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.aps as aps
import json

# Test the impact of the bug
print("=== Testing LoggingFilter with string vs integer QspThreshold ===\n")

# Case 1: Integer input
filter1 = aps.LoggingFilter(QspThreshold=100)
print(f"With integer 100:")
print(f"  filter1.QspThreshold = {filter1.QspThreshold!r}")
print(f"  type = {type(filter1.QspThreshold)}")
print(f"  to_dict() = {filter1.to_dict()}")

# Case 2: String input
filter2 = aps.LoggingFilter(QspThreshold='100')
print(f"\nWith string '100':")
print(f"  filter2.QspThreshold = {filter2.QspThreshold!r}")
print(f"  type = {type(filter2.QspThreshold)}")
print(f"  to_dict() = {filter2.to_dict()}")

# Test JSON serialization (CloudFormation templates are JSON)
print("\n=== JSON Serialization ===")
print(f"filter1 (integer): {json.dumps(filter1.to_dict())}")
print(f"filter2 (string):  {json.dumps(filter2.to_dict())}")

# Test WorkspaceConfiguration with RetentionPeriodInDays
print("\n=== Testing WorkspaceConfiguration ===")
config1 = aps.WorkspaceConfiguration(RetentionPeriodInDays=30)
config2 = aps.WorkspaceConfiguration(RetentionPeriodInDays='30')

print(f"With integer 30: {config1.to_dict()}")
print(f"With string '30': {config2.to_dict()}")

# Test comparison
print("\n=== Type Comparison Issues ===")
print(f"filter1.QspThreshold == filter2.QspThreshold: {filter1.QspThreshold == filter2.QspThreshold}")
print(f"filter1.QspThreshold == 100: {filter1.QspThreshold == 100}")
print(f"filter2.QspThreshold == 100: {filter2.QspThreshold == 100}")
print(f"filter2.QspThreshold == '100': {filter2.QspThreshold == '100'}")