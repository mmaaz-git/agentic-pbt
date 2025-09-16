#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import copier._vcs as vcs
import re

print("=== Analyzing properties from code ===\n")

# 1. get_repo function
print("1. get_repo() properties:")
print("   - Takes URL patterns and transforms them")
print("   - gh:xxx -> https://github.com/xxx.git")
print("   - gl:xxx -> https://gitlab.com/xxx.git")
print("   - Returns None if not a valid git repo")
print("   Evidence: REPLACEMENTS patterns and implementation at lines 109-126")
print()

# 2. valid_version function
print("2. valid_version() properties:")
print("   - Should return True for valid PEP 440 versions")
print("   - Should return False for invalid versions")
print("   Evidence: Docstring says 'Tell if a string is a valid PEP 440 version'")
print()

# 3. is_git_repo_root function  
print("3. is_git_repo_root() properties:")
print("   - Returns True only if path/.git exists and is inside git dir")
print("   - Returns False otherwise")
print("   Evidence: Implementation checks .git directory at lines 54-60")
print()

# Test the replacements
print("=== Testing URL patterns ===")
test_urls = [
    "gh:copier-org/copier",
    "gh:copier-org/copier.git",
    "gl:copier-org/copier",
    "gl:copier-org/copier.git",
    "git@github.com:user/repo.git",
    "https://github.com/user/repo",
]

for url in test_urls:
    result = vcs.get_repo(url)
    print(f"  get_repo('{url}') -> {result}")