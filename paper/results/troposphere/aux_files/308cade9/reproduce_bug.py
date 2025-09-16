#!/usr/bin/env python3
"""Minimal reproduction of the validate_backup_selection bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import If
from troposphere.backup import BackupSelectionResourceType

# The bug: When both ListOfTags and Resources are CloudFormation If objects,
# the validation incorrectly allows both to be present, violating the 
# "exactly one" requirement.

# Create If conditions (CloudFormation conditionals)
condition1 = If("UseTagSelection", [{"ConditionKey": "env", "ConditionType": "STRINGEQUALS", "ConditionValue": "prod"}], [])
condition2 = If("UseResourceSelection", ["arn:aws:ec2:*:*:volume/*"], [])

# This should fail validation because both ListOfTags and Resources are specified
# But it doesn't fail when both are If objects
selection = BackupSelectionResourceType(
    IamRoleArn="arn:aws:iam::123456789012:role/BackupRole",
    SelectionName="BuggySelection",
    ListOfTags=condition1,  # If object
    Resources=condition2     # If object
)

# This should raise ValueError but doesn't
selection.validate()
print("BUG: Validation passed when it should have failed!")
print("Both ListOfTags and Resources were specified (as If objects).")
print("This violates the 'exactly one' constraint.")