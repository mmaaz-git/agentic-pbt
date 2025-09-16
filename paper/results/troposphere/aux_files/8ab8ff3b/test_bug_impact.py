#!/usr/bin/env python3
"""Test the impact of the boolean validator bug in real usage."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import codestar

# Test 1: Can we create a GitHubRepository with float values for boolean fields?
print("Test 1: Creating GitHubRepository with float values for boolean fields...")
try:
    repo = codestar.GitHubRepository(
        title="TestRepo",
        RepositoryName="test-repo",
        RepositoryOwner="owner",
        EnableIssues=1.0,  # Float instead of boolean
        IsPrivate=0.0      # Float instead of boolean
    )
    print(f"  Created successfully")
    print(f"  EnableIssues: {repo.EnableIssues} (type: {type(repo.EnableIssues)})")
    print(f"  IsPrivate: {repo.IsPrivate} (type: {type(repo.IsPrivate)})")
    
    # Check JSON output
    json_output = repo.to_json()
    print(f"  JSON output snippet: ...EnableIssues\": {repo.EnableIssues!r}...")
except Exception as e:
    print(f"  Failed: {e}")

# Test 2: What about non-0/1 floats?
print("\nTest 2: Using non-0/1 float values...")
try:
    repo2 = codestar.GitHubRepository(
        title="TestRepo2",
        RepositoryName="test-repo2",
        RepositoryOwner="owner2",
        EnableIssues=0.5  # Non-standard float
    )
    print(f"  Created successfully")
    print(f"  EnableIssues: {repo2.EnableIssues}")
except Exception as e:
    print(f"  Failed as expected: {e}")

# Test 3: Show that this could lead to unexpected behavior
print("\nTest 3: Demonstrating potential confusion...")
print("  Developer might accidentally pass 1.0 from a calculation:")
issues_count = 5.0
enable_issues = issues_count / 5.0  # Results in 1.0
print(f"  enable_issues = {enable_issues} (type: {type(enable_issues)})")

try:
    repo3 = codestar.GitHubRepository(
        title="TestRepo3",
        RepositoryName="test-repo3",
        RepositoryOwner="owner3",
        EnableIssues=enable_issues
    )
    print(f"  Unexpectedly accepted float {enable_issues} as boolean")
    print(f"  This violates the type contract - EnableIssues should be strictly boolean")
except Exception as e:
    print(f"  Correctly rejected: {e}")