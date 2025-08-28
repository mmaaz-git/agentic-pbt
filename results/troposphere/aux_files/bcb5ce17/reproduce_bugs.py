#!/usr/bin/env python3
"""Minimal reproductions of bugs found in troposphere.systemsmanagersap"""

import troposphere.systemsmanagersap as sap

print("=== Bug 1: from_dict cannot handle output of to_dict ===")
print("This violates the round-trip property that from_dict(to_dict(x)) should work")

# Create a simple Application
app1 = sap.Application('MyApp', ApplicationId='app-123', ApplicationType='SAP/HANA')
print(f"Created Application: {app1.title}")

# Convert to dict - this works
full_dict = app1.to_dict()
print(f"to_dict output: {full_dict}")

# Try to create from the full dict - this fails
try:
    app2 = sap.Application.from_dict('MyApp2', full_dict)
    print("SUCCESS: from_dict handled to_dict output")
except AttributeError as e:
    print(f"FAILURE: {e}")
    print("The from_dict method expects just the properties, not the full dict structure")

# Show the workaround
print("\nWorkaround: Extract just the Properties:")
props_only = full_dict['Properties']
app3 = sap.Application.from_dict('MyApp3', props_only)
print(f"SUCCESS: Created app from properties only: {app3.title}")

print("\n=== Bug 2: Title validation is overly restrictive ===")
print("Underscores are commonly used in CloudFormation resource names but are rejected")

# Try creating with underscore in title
try:
    app_underscore = sap.Application('My_App', ApplicationId='app-123', ApplicationType='SAP/HANA')
    print(f"SUCCESS: Created app with underscore: {app_underscore.title}")
except ValueError as e:
    print(f"FAILURE: {e}")

# Try from_dict with underscore
try:
    props = {'ApplicationId': 'app-456', 'ApplicationType': 'SAP/HANA'}
    cred = sap.Credential.from_dict('cred_title', {'CredentialType': 'ADMIN'})
    print(f"SUCCESS: Created credential with underscore: {cred.title}")
except ValueError as e:
    print(f"FAILURE: {e}")

print("\n=== Impact Analysis ===")
print("1. The round-trip bug breaks serialization/deserialization workflows")
print("2. The title validation bug prevents common CloudFormation naming patterns")
print("3. Both bugs affect all AWS resource classes in the module (Application, Credential, ComponentInfo)")