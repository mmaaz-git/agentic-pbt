#!/usr/bin/env python3
"""
Minimal reproduction of troposphere None handling bug.
This demonstrates that optional properties cannot be explicitly set to None.
"""

import troposphere.cleanrooms as cleanrooms

# This fails with TypeError
try:
    obj = cleanrooms.AnalysisParameter(
        Name="test",
        Type="STRING", 
        DefaultValue=None  # Optional property set to None
    )
    print("Success: Created object with None optional property")
except TypeError as e:
    print(f"BUG: {e}")

# This works - not setting the optional property
obj2 = cleanrooms.AnalysisParameter(
    Name="test",
    Type="STRING"
    # DefaultValue not set
)
print(f"Workaround works: {obj2.to_dict()}")
