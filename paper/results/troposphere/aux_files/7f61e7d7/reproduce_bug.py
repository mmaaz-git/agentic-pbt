#!/usr/bin/env python3
"""Minimal reproduction of the round-trip bug in troposphere.workspaces"""

import troposphere.workspaces as ws

# Create a Workspace object
workspace = ws.Workspace(
    'MyWorkspace',
    BundleId='bundle-123',
    DirectoryId='dir-456',
    UserName='testuser'
)

print("Original workspace created successfully")
print(f"  BundleId: {workspace.BundleId}")
print(f"  DirectoryId: {workspace.DirectoryId}")
print(f"  UserName: {workspace.UserName}")

# Convert to dict
ws_dict = workspace.to_dict()
print(f"\nto_dict() output: {ws_dict}")

# Try to recreate from the dict - THIS FAILS
print("\nAttempting to recreate workspace from to_dict() output...")
try:
    recreated = ws.Workspace.from_dict('RecreatedWorkspace', ws_dict)
    print("Success! Workspace recreated")
except AttributeError as e:
    print(f"ERROR: {e}")
    print("\nThe bug: to_dict() wraps properties in 'Properties' key,")
    print("but from_dict() expects the properties directly.")
    
    # Show the workaround
    print("\nWorkaround: Extract just the Properties:")
    recreated = ws.Workspace.from_dict('RecreatedWorkspace', ws_dict['Properties'])
    print(f"Success with workaround! BundleId: {recreated.BundleId}")