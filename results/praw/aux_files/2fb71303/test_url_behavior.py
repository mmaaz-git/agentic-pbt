#!/usr/bin/env python3
"""Test if the URL parsing behavior is correct for Reddit's actual URL structure."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from praw.models.reddit.comment import Comment
from praw.exceptions import InvalidURL
from urllib.parse import urlparse

# Real Reddit URL patterns
real_reddit_patterns = [
    # Standard comment URL
    "https://www.reddit.com/r/Python/comments/abc123/some_title/def456",
    # With query parameters (common for tracking)
    "https://www.reddit.com/r/Python/comments/abc123/some_title/def456?context=3",
    # With fragment (for anchoring)
    "https://www.reddit.com/r/Python/comments/abc123/some_title/def456#t1_def456",
    # Old reddit
    "https://old.reddit.com/r/Python/comments/abc123/some_title/def456",
    # Mobile
    "https://m.reddit.com/r/Python/comments/abc123/some_title/def456",
]

print("Testing with realistic Reddit URL patterns:")
print("=" * 60)

for url in real_reddit_patterns:
    print(f"\nURL: {url}")
    parsed = urlparse(url)
    print(f"  Path: {parsed.path}")
    print(f"  Query: {parsed.query}")
    print(f"  Fragment: {parsed.fragment}")
    
    try:
        comment_id = Comment.id_from_url(url)
        print(f"  Extracted ID: {comment_id}")
        
        # The comment ID should always be 'def456' for our test URLs
        if comment_id != "def456":
            print(f"  WARNING: Expected 'def456', got '{comment_id}'")
    except InvalidURL as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("Analysis:")
print("-" * 60)
print("The behavior of stripping query parameters and fragments is CORRECT.")
print("Reddit comment IDs are alphanumeric strings that don't contain special")
print("characters like '?', '#', or '&'. These characters in URLs serve other")
print("purposes (query parameters and fragments) and are not part of the ID.")
print("\nThis is NOT a bug - it's the correct behavior for parsing Reddit URLs.")