#!/usr/bin/env python3
"""Minimal reproduction of the mutable constants bug in storage3."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

# Scenario: Two different parts of an application use storage3
# Part A modifies what it thinks is a local copy
# Part B gets affected unexpectedly

# Part A: Admin panel code
from storage3.constants import DEFAULT_SEARCH_OPTIONS

print("Part A - Admin panel customizing search options")
print(f"Initial limit: {DEFAULT_SEARCH_OPTIONS['limit']}")

# Admin thinks they're customizing their own search
admin_options = DEFAULT_SEARCH_OPTIONS
admin_options["limit"] = 10000  # Admin wants to see more results
print(f"Admin set limit to: {admin_options['limit']}")

# Part B: User-facing API (different module/file)
from storage3.constants import DEFAULT_SEARCH_OPTIONS as user_defaults

print("\nPart B - User API expecting default options")
print(f"User API sees limit: {user_defaults['limit']}")  # Should be 100, but is 10000!

# This violates the principle of constants being immutable
# The admin's changes affected the user API unexpectedly
assert user_defaults["limit"] == 10000, "Bug: Constants are mutable!"

print("\nBUG CONFIRMED: Modifying DEFAULT_SEARCH_OPTIONS in one place affects all uses!")
print("This breaks encapsulation and can cause hard-to-debug issues.")

# The correct behavior would be for DEFAULT_SEARCH_OPTIONS to be immutable
# Each use should get a fresh copy, not a shared mutable reference