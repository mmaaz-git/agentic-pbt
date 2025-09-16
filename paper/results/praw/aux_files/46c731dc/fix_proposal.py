"""Proposed fix for the objectify bug."""

# The bug is on line 237 of objector.py where it checks:
#   if "json" in data and "errors" in data["json"]:
# 
# This fails when data is an integer or other non-dict type.
# The fix is to add a type check before attempting dict operations.

# Current buggy code (lines 235-240):
"""
if isinstance(data, bool):  # Reddit.username_available
    return data
if "json" in data and "errors" in data["json"]:  # BUG: assumes data is dict-like
    errors = data["json"]["errors"]
    if len(errors) > 0:
        raise RedditAPIException(errors)
"""

# Fixed code:
"""
if isinstance(data, bool):  # Reddit.username_available
    return data
if isinstance(data, dict) and "json" in data and "errors" in data["json"]:
    errors = data["json"]["errors"]
    if len(errors) > 0:
        raise RedditAPIException(errors)
"""

# Alternative fix that's more comprehensive:
"""
if isinstance(data, bool):  # Reddit.username_available
    return data
# Check if data is dict-like before attempting dict operations
if not isinstance(data, dict):
    return data  # Return primitives as-is
if "json" in data and "errors" in data["json"]:
    errors = data["json"]["errors"]
    if len(errors) > 0:
        raise RedditAPIException(errors)
"""