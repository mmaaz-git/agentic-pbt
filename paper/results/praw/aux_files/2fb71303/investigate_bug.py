#!/usr/bin/env python3
"""Investigate the Comment.id_from_url bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from praw.models.reddit.comment import Comment
from praw.exceptions import InvalidURL

# Test cases that might reveal the bug
test_cases = [
    ("0#", "https://www.reddit.com/r/test/comments/abc123/title/0#"),
    ("0#", "https://www.reddit.com/r/test/comments/abc123/title/0#/"),
    ("test#anchor", "https://www.reddit.com/r/test/comments/abc123/title/test#anchor"),
    ("test?query=1", "https://www.reddit.com/r/test/comments/abc123/title/test?query=1"),
    ("test&param", "https://www.reddit.com/r/test/comments/abc123/title/test&param"),
]

print("Testing Comment.id_from_url with special characters:")
print("-" * 50)

for expected_id, url in test_cases:
    try:
        result = Comment.id_from_url(url)
        matches = result == expected_id
        print(f"URL: {url}")
        print(f"  Expected: {expected_id}")
        print(f"  Got: {result}")
        print(f"  Match: {matches}")
        if not matches:
            print(f"  >>> BUG: Result doesn't match expected!")
    except InvalidURL as e:
        print(f"URL: {url}")
        print(f"  Raised InvalidURL: {e}")
    print()

# Let's also check the internal URL parsing
print("\nChecking how URL fragments and query params are handled:")
print("-" * 50)

# Test with a simple case first
simple_url = "https://www.reddit.com/r/test/comments/abc123/title/def456"
print(f"Simple URL: {simple_url}")
print(f"  Result: {Comment.id_from_url(simple_url)}")
print()

# Test with fragment
fragment_url = "https://www.reddit.com/r/test/comments/abc123/title/def456#fragment"
print(f"URL with fragment: {fragment_url}")
try:
    result = Comment.id_from_url(fragment_url)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")
print()

# Test with query
query_url = "https://www.reddit.com/r/test/comments/abc123/title/def456?query=value"
print(f"URL with query: {query_url}")
try:
    result = Comment.id_from_url(query_url)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")