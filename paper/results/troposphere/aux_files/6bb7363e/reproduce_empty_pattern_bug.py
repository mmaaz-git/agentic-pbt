"""Reproduce the empty Pattern bug in PackageGroup"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codeartifact as codeartifact

# Pattern is marked as required (True) in the props definition
# But it accepts empty string which should be invalid

pg = codeartifact.PackageGroup(
    title="TestPackageGroup",
    DomainName="test-domain",
    Pattern=""  # Empty pattern - should this be allowed?
)

# Convert to dict to trigger validation
pg_dict = pg.to_dict()

print(f"PackageGroup created with empty Pattern: {pg_dict}")
print(f"Pattern value: '{pg_dict['Properties']['Pattern']}'")

# The issue: Empty string passes validation for a required field
# This could cause problems in CloudFormation as empty patterns may not be valid