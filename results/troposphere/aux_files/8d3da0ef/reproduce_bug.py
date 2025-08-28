#!/usr/bin/env python3
"""
Minimal reproduction of the to_dict/from_dict round-trip bug in troposphere
"""

import troposphere.resourceexplorer2 as re2

# Create a View object
view = re2.View('MyView', ViewName='test-view')

# Convert to dict
view_dict = view.to_dict()
print("Original to_dict output:")
print(view_dict)
# Output: {'Properties': {'ViewName': 'test-view'}, 'Type': 'AWS::ResourceExplorer2::View'}

# Try to recreate from the dict
try:
    recreated_view = re2.View.from_dict('MyView', view_dict)
    print("\nSuccessfully recreated view")
except AttributeError as e:
    print(f"\nFailed to recreate: {e}")
    # Error: Object type View does not have a Properties property.
    
    # The workaround - use just the Properties content
    print("\nWorkaround: Using just the Properties content...")
    recreated_view = re2.View.from_dict('MyView', view_dict['Properties'])
    print("Successfully recreated with workaround")
    
    # But the round-trip still fails
    recreated_dict = recreated_view.to_dict()
    print(f"\nOriginal dict == Recreated dict: {view_dict == recreated_dict}")
    print(f"Original: {view_dict}")
    print(f"Recreated: {recreated_dict}")